"""
MCQ generation via Gemini.
Generates multiple-choice questions based on position + tech stack.
"""
import json
import re
from app.core.logging import log
from app.core import llm_service
from app.models.invite import MCQQuestion, MCQOption


async def generate_mcq_questions(
    position: str,
    tech_stack: str,
    difficulty: str,
    num_questions: int,
) -> list[MCQQuestion]:
    """Use Gemini to generate MCQ questions tailored to the role."""

    difficulty_desc = {
        "junior": "foundational concepts, syntax, and basic patterns",
        "mid": "design patterns, debugging, and architectural tradeoffs",
        "senior": "system design, scalability, and senior-level technical decisions",
    }.get(difficulty, "general concepts")

    prompt = f"""You are a software engineering interviewer creating a technical assessment.

Generate exactly {num_questions} multiple-choice questions for a software engineering job interview.

Job Role: {position}
Technologies: {tech_stack}
Seniority Level: {difficulty} — questions should cover {difficulty_desc}

Requirements:
- Each question tests a specific, practical technical concept
- Each question has exactly 4 answer options labeled A, B, C, D
- Exactly one option is correct; the others are plausible but incorrect
- Questions must be unambiguous and professionally worded
- Cover different topics across the listed technologies

Return ONLY a valid JSON array with no markdown, no code fences, no explanation.
CRITICAL: NEVER include trailing commas in your JSON.
[
  {{
    "id": 1,
    "question": "What does the Python keyword 'yield' do in a function?",
    "topic": "Python",
    "options": [
      {{"key": "A", "text": "Returns a value and terminates the function"}},
      {{"key": "B", "text": "Pauses the function and returns a value to the caller, resuming on next call"}},
      {{"key": "C", "text": "Declares a variable as a generator type"}},
      {{"key": "D", "text": "Raises a StopIteration exception"}}
    ],
    "correct_answer": "B"
  }}
]"""

    result = await llm_service.generate_text(prompt)
    # Strip any accidental markdown fences
    cleaned = re.sub(r"```(?:json)?", "", result).strip().rstrip("`").strip()
    # Strip trailing commas that break strict JSON parsers
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)

    try:
        raw_questions = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse MCQ JSON: {e}\nRaw output: {cleaned}")
        raise
        
    questions = []
    for q in raw_questions:
        questions.append(MCQQuestion(
            id=q["id"],
            question=q["question"],
            topic=q.get("topic", "General"),
            options=[MCQOption(key=o["key"], text=o["text"]) for o in q["options"]],
            correct_answer=q["correct_answer"],
        ))
    log.info(f"Generated {len(questions)} MCQ questions for '{position}' ({difficulty})")
    return questions


def score_answers(questions: list[MCQQuestion], raw_answers: list[dict]) -> tuple[int, list]:
    """Score submitted answers. Returns (score_0_to_100, list_of_CandidateAnswer)."""
    from app.models.invite import CandidateAnswer
    q_map = {q.id: q for q in questions}
    scored = []
    correct = 0
    for ans in raw_answers:
        qid = ans.get("question_id")
        selected = ans.get("selected", "")
        q = q_map.get(qid)
        is_correct = bool(q and q.correct_answer == selected)
        if is_correct:
            correct += 1
        scored.append(CandidateAnswer(
            question_id=qid,
            selected=selected,
            is_correct=is_correct,
        ))
    score = round((correct / len(questions)) * 100) if questions else 0
    return score, scored
