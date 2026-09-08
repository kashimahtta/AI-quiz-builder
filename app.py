from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass
from typing import Any

import streamlit as st


@dataclass
class Question:
    prompt: str
    options: list[str]
    answer: str
    explanation: str
    source: str


st.set_page_config(
    page_title="Quizloom | AI Quiz Builder",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# A warm, editorial visual system keeps the builder readable while giving it a
# distinct identity from a default Streamlit dashboard.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --ink: #182329;
  --muted: #66747a;
  --paper: #f7f5ef;
  --panel: #fffdf8;
  --line: #dfe4dd;
  --mint: #b9e8d4;
  --mint-strong: #267a5a;
  --coral: #ff8066;
  --yellow: #f3d56b;
}

html, body, [class*="css"] { font-family: 'Manrope', sans-serif; color: var(--ink); }
.stApp { background: radial-gradient(circle at 15% 0%, #fffdf1 0, transparent 34%), var(--paper); }
.block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }
[data-testid="stSidebar"] { background: #1d2b2e; }
[data-testid="stSidebar"] * { color: #edf7f0 !important; }
[data-testid="stSidebar"] .stRadio label { padding: .38rem .1rem; }

.eyebrow { font-family: 'DM Mono', monospace; color: var(--mint-strong); font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .55rem; }
.hero-title { font-size: clamp(2.25rem, 5vw, 4.5rem); line-height: .98; letter-spacing: -.065em; font-weight: 800; max-width: 720px; margin: 0; }
.hero-title span { color: var(--coral); }
.hero-copy { color: var(--muted); max-width: 620px; font-size: 1.03rem; margin-top: 1rem; }
.section-label { font-family: 'DM Mono', monospace; font-size: .72rem; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin: 1.8rem 0 .65rem; }
.metric-strip { display: flex; gap: .65rem; flex-wrap: wrap; margin: 1.5rem 0 .4rem; }
.metric { border: 1px solid var(--line); background: rgba(255,253,248,.76); padding: .72rem 1rem; min-width: 120px; border-radius: 12px; }
.metric strong { display:block; font-size: 1.25rem; }
.metric small { color: var(--muted); }
.question-card { background: var(--panel); color: #000000 !important; border: 1px solid var(--line); border-left: 4px solid var(--mint-strong); padding: 1.1rem 1.2rem; border-radius: 0 12px 12px 0; margin: .75rem 0; }
.question-card strong, .question-card small { color: #000000 !important; }
.question-card .tag { font-family:'DM Mono', monospace; font-size:.7rem; color:var(--mint-strong); text-transform:uppercase; }
.quiz-question, .quiz-question strong { color: #000000 !important; }
.stButton > button { border-radius: 9px; border: 1px solid #1d2b2e; font-weight: 700; padding: .65rem 1.05rem; }
.stButton > button[kind="primary"] { background: var(--coral); border-color: var(--coral); color: #fff; }
div[data-testid="stForm"] { background: var(--panel); border: 1px solid var(--line); padding: 1.2rem; border-radius: 14px; }
[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--line); padding: .8rem; border-radius: 12px; }
code { font-family: 'DM Mono', monospace; }
</style>
""",
    unsafe_allow_html=True,
)


def clean_notes(notes: str) -> list[str]:
    return [line.strip(" -•\t") for line in notes.splitlines() if line.strip()]


def topic_words(topic: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", topic.lower())
    return list(dict.fromkeys(words)) or ["the subject"]


def build_question(topic: str, difficulty: str, index: int, notes: list[str], rng: random.Random) -> Question:
    focus = notes[index % len(notes)] if notes else f"a core idea in {topic}"
    words = topic_words(topic)
    anchor = words[index % len(words)].capitalize()
    distractors = [
        f"An unrelated detail about {topic}",
        f"A common misconception about {topic}",
        f"A later consequence rather than the main idea",
        f"A definition from a different field",
    ]
    templates: list[tuple[str, str, str]] = [
        (
            f"Which statement best captures the key idea behind {anchor} in {topic}?",
            focus,
            f"The study note points directly to this idea: {focus}.",
        ),
        (
            f"A learner is reviewing {topic}. Which option should they remember first?",
            focus,
            f"This is the central takeaway supplied in the notes: {focus}.",
        ),
        (
            f"What is the most accurate interpretation of this {topic} concept?",
            focus,
            f"The best interpretation follows the provided material: {focus}.",
        ),
    ]
    prompt, correct, explanation = templates[index % len(templates)]
    options = [correct] + distractors[:3]
    rng.shuffle(options)
    return Question(prompt, options, correct, explanation, "Generated from your topic and study notes")


def generate_quiz(topic: str, difficulty: str, count: int, notes_text: str) -> list[Question]:
    notes = clean_notes(notes_text)
    rng = random.Random(f"{topic}:{difficulty}:{count}:{notes_text}")
    questions = [build_question(topic, difficulty, i, notes, rng) for i in range(count)]
    return questions


def quiz_json(questions: list[Question]) -> str:
    return json.dumps([asdict(question) for question in questions], indent=2)


def initialize_state() -> None:
    st.session_state.setdefault("questions", [])
    st.session_state.setdefault("answers", {})
    st.session_state.setdefault("submitted", False)
    st.session_state.setdefault("quiz_title", "Untitled quiz")


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## ✦ Quizloom")
        st.caption("A focused studio for turning ideas into practice.")
        view = st.radio("Workspace", ["Build", "Take quiz", "Results"], label_visibility="collapsed")
        st.divider()
        st.markdown("**Workflow**")
        st.caption("1. Set a topic and notes\n\n2. Generate a question set\n\n3. Take it and review the why")
        st.divider()
        st.caption("Offline generation enabled")
    return view


def render_header() -> None:
    st.markdown('<div class="eyebrow">AI-assisted study studio</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Make learning<br><span>stick.</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-copy">Turn a topic, a few notes, and a little curiosity into a quiz you can actually use.</p>', unsafe_allow_html=True)


def render_build() -> None:
    render_header()
    questions: list[Question] = st.session_state.questions
    st.markdown('<div class="section-label">01 / Shape your quiz</div>', unsafe_allow_html=True)
    demo_prompt = """Topic: Photosynthesis

Study notes:
Plants, algae, and cyanobacteria use light energy to produce chemical energy.
The light-dependent reactions split water and release oxygen.
The Calvin cycle uses carbon dioxide, ATP, and NADPH to form sugars.

Expected demo answer:
Photosynthesis converts light energy into chemical energy. In the light-dependent reactions, water is split and oxygen is released. The Calvin cycle then uses carbon dioxide, ATP, and NADPH to help form sugars."""
    with st.expander("See a demo prompt and answer"):
        st.caption("This is the kind of text document viewers can paste into the builder.")
        st.code(demo_prompt, language="text")
        st.download_button(
            "Download demo prompt",
            demo_prompt,
            file_name="quizloom_demo_prompt.txt",
            mime="text/plain",
        )
    with st.form("quiz_builder"):
        topic = st.text_input("What are you learning?", placeholder="e.g. Photosynthesis, World War II, Python decorators")
        notes = st.text_area(
            "Study notes (one idea per line)",
            placeholder="Paste notes here for more grounded questions...\nExample: Plants convert light energy into chemical energy.",
            height=150,
        )
        left, right = st.columns(2)
        with left:
            difficulty = st.select_slider("Difficulty", options=["Warm-up", "Focused", "Stretch"], value="Focused")
        with right:
            count = st.slider("Number of questions", min_value=3, max_value=10, value=5)
        submitted = st.form_submit_button("Generate quiz  →", type="primary", use_container_width=True)

    if submitted:
        if not topic.strip():
            st.error("Add a topic first so the builder has something to work with.")
            return
        st.session_state.questions = generate_quiz(topic.strip(), difficulty, count, notes)
        st.session_state.quiz_title = topic.strip().title()
        st.session_state.answers = {}
        st.session_state.submitted = False
        st.success(f"Built {count} questions for {topic.strip()}.")
        st.rerun()

    if questions:
        st.markdown('<div class="section-label">02 / Your question set</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-strip"><div class="metric"><strong>{len(questions)}</strong><small>questions</small></div><div class="metric"><strong>{st.session_state.quiz_title}</strong><small>topic</small></div><div class="metric"><strong>Offline</strong><small>generation</small></div></div>',
            unsafe_allow_html=True,
        )
        for number, question in enumerate(questions, start=1):
            st.markdown(f'<div class="question-card"><div class="tag">Question {number:02d}</div><strong>{question.prompt}</strong><br><small>{question.source}</small></div>', unsafe_allow_html=True)
        st.download_button("Download question set", quiz_json(questions), file_name="quizloom_questions.json", mime="application/json")
    else:
        st.info("Your generated quiz will appear here. Start with a topic or paste in notes.")


def render_take_quiz() -> None:
    questions: list[Question] = st.session_state.questions
    st.markdown('<div class="eyebrow">Active session</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="hero-title">{st.session_state.quiz_title}<br><span>quiz.</span></h1>', unsafe_allow_html=True)
    if not questions:
        st.warning("Build a quiz first, then come back here to take it.")
        return
    st.caption(f"{len(questions)} questions · choose one answer per question")
    with st.form("take_quiz"):
        for number, question in enumerate(questions, start=1):
            st.markdown(f'<div class="quiz-question"><strong>{number:02d}  {question.prompt}</strong></div>', unsafe_allow_html=True)
            choice = st.radio("Answer", question.options, key=f"answer_{number}", label_visibility="collapsed")
            st.divider()
        submitted = st.form_submit_button("Check my answers  →", type="primary", use_container_width=True)
    if submitted:
        st.session_state.answers = {str(i): st.session_state[f"answer_{i}"] for i in range(1, len(questions) + 1)}
        st.session_state.submitted = True
        st.success("Answers checked. Open Results to see your score and the reasoning.")


def render_results() -> None:
    questions: list[Question] = st.session_state.questions
    st.markdown('<div class="eyebrow">Review desk</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">See what<br><span>stuck.</span></h1>', unsafe_allow_html=True)
    if not questions:
        st.info("There are no results yet. Build a quiz to begin.")
        return
    if not st.session_state.submitted:
        st.info("Take the quiz first. Your score and explanations will appear here.")
        return
    score = sum(st.session_state.answers.get(str(i)) == question.answer for i, question in enumerate(questions, start=1))
    percentage = round(score / len(questions) * 100)
    st.metric("Score", f"{score} / {len(questions)}", f"{percentage}%")
    for number, question in enumerate(questions, start=1):
        selected = st.session_state.answers.get(str(number), "")
        is_correct = selected == question.answer
        icon = "✓" if is_correct else "×"
        st.markdown(f"**{icon} {number:02d}  {question.prompt}**")
        if is_correct:
            st.success(f"Correct: {question.answer}")
        else:
            st.error(f"You chose: {selected}")
            st.info(f"Correct answer: {question.answer}")
        st.caption(question.explanation)


initialize_state()
view = render_sidebar()
if view == "Build":
    render_build()
elif view == "Take quiz":
    render_take_quiz()
else:
    render_results()
