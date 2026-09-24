import json
from typing import AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
import groq

from app.config import settings
from app.core.logging import log

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

def _model(pro: bool = False) -> genai.GenerativeModel:
    name = settings.gemini_pro_model if pro else settings.gemini_model
    return genai.GenerativeModel(name, generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=1024))

@retry(
    retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
    stop=stop_after_attempt(2),
    wait=wait_exponential(min=1, max=3),
)
async def _generate_text_gemini(prompt: str, system: str | None = None) -> str:
    """Single shot generation with auto-retry on rate limits."""
    m = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=system,
        generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=4096)
    )
    response = await m.generate_content_async(prompt)

    # Check finish_reason before accessing .text
    # 1=STOP (normal), 2=SAFETY, 3=RECITATION, 4=OTHER, 5=MAX_TOKENS
    candidate = response.candidates[0] if response.candidates else None
    finish_reason = candidate.finish_reason if candidate else None
    if finish_reason == 2:
        raise ValueError(
            "Gemini blocked this prompt due to safety filters. "
            "Try rephrasing the tech stack or position name."
        )
    if not response.parts:
        raise ValueError(f"Gemini returned no content (finish_reason={finish_reason}).")

    return response.text.strip()

async def _generate_text_groq(prompt: str, system: str | None = None) -> str:
    """Generation using Groq's fast Llama 3 70B model."""
    client = groq.AsyncGroq(api_key=settings.groq_api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()

async def generate_text(prompt: str, system: str | None = None) -> str:
    """Primary text generation. Tries Gemini, falls back to Groq on failure."""
    if settings.gemini_api_key:
        try:
            return await _generate_text_gemini(prompt, system)
        except Exception as e:
            if settings.groq_api_key:
                log.warning(f"Gemini generation failed ({e}), falling back to Groq.")
                return await _generate_text_groq(prompt, system)
            raise e
    elif settings.groq_api_key:
        return await _generate_text_groq(prompt, system)
    else:
        raise ValueError("No LLM API keys configured (set GEMINI_API_KEY or GROQ_API_KEY).")

async def stream_text(prompt: str, system: str | None = None) -> AsyncGenerator[str, None]:
    """Yields text chunks as Gemini produces them, powers the streaming UI"""
    m = genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=system,
        generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=1024)
    ) if system else _model()
    async for chunk in await m.generate_content_async(prompt, stream=True):
        if chunk.text:
            yield chunk.text

async def generate_technical_question(tech_stack: str, question_number: int) -> str:
    system = "You are a senior technical interviewer. Generate precise, fair interview questions."
    difficulty = (
        "a fundamental concept" if question_number <= 2
        else "system design or architecture" if question_number <= 4
        else "a debugging or trade-offs scenario"
    )
    prompt = f"""Generate technical interview question {question_number} of 5.

Candidate's tech stack: {tech_stack}

Requirements:
- Test practical real-world knowledge
- Be specific to 1-2 technologies in their stack
- This question should focus on: {difficulty}
- Return ONLY the question, no numbering or preamble."""
    return await generate_text(prompt, system=system)


async def score_technical_answers(tech_stack: str, qa_pairs: list[dict]) -> list[dict]:
    """Use Gemini Pro to evaluate all 5 answers and add score + rationale."""
    qa_text = "\n\n".join(
        f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}"
        for i, qa in enumerate(qa_pairs)
    )
    prompt = f"""Evaluate these interview answers. Candidate stack: {tech_stack}

{qa_text}

Score each 1–5:
5 = Excellent · 4 = Good · 3 = Adequate · 2 = Weak · 1 = Poor/No answer

Return ONLY a JSON array:
[{{"question_number": 1, "score": 4, "score_rationale": "brief reason"}}]"""

    result = await generate_text(prompt)
    result = result.strip().removeprefix("```json").removesuffix("```").strip()
    scores = json.loads(result)
    score_map = {s["question_number"]: s for s in scores}
    for i, qa in enumerate(qa_pairs):
        s = score_map.get(i + 1, {})
        qa["score"] = s.get("score")
        qa["score_rationale"] = s.get("score_rationale")
    return qa_pairs


async def check_relevance(message: str, context: str) -> bool:
    prompt = f"""Is this message relevant to a job recruitment interview?
Context: {context}
Message: "{message}"
Relevant = providing info, answering questions, asking about the process.
Irrelevant = trivia, off-topic, unrelated requests.
Reply with exactly one word: RELEVANT or IRRELEVANT"""
    try:
        result = await generate_text(prompt)
        log.debug(f"check_relevance raw='{result}'")
        return "RELEVANT" in result.upper()
    except Exception as e:
        log.warning(f"check_relevance failed ({e}), defaulting to RELEVANT")
        return True   # fail open


async def extract_field_value(message: str, field_name: str) -> str | int | None:
    descriptions = {
        "name": "the person's full name (string)",
        "email": "a valid email address (string)",
        "phone": "phone number digits only (string)",
        "years_experience": "years of professional experience, 0 for fresh graduate (integer)",
        "desired_position": "job title or role applying for (string)",
        "location": "current city or country (string)",
        "tech_stack": "comma-separated list of technologies (string)",
    }
    prompt = f"""Extract {descriptions[field_name]} from: "{message}"
If not present, return null.
Return ONLY valid JSON: {{"value": <extracted_value_or_null>}}"""
    try:
        result = await generate_text(prompt)
        log.debug(f"extract_field_value field={field_name!r} raw='{result}'")
        cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        extracted = parsed.get("value")
        log.debug(f"extract_field_value field={field_name!r} extracted={extracted!r}")
        return extracted
    except Exception as e:
        log.error(f"extract_field_value FAILED for field={field_name!r} message={message!r}: {e}")
        return None
