import json
from datetime import datetime
from app.models.interview import (
    InterviewSession, InterviewStage, TechnicalQA, Message
)
from app.core import llm_service
from app.core.validation import validate_field

FIELD_ORDER = ["name", "email", "phone", "years_experience",
               "desired_position", "location", "tech_stack"]

FIELD_PROMPTS = {
    "name": "What's your full name?",
    "email": "What's your email address?",
    "phone": "What's your phone number? (include country code if outside India)",
    "years_experience": "How many years of professional experience do you have? (enter 0 if you're a fresh graduate)",
    "desired_position": "What role are you applying for? (e.g., Backend Engineer, Data Analyst)",
    "location": "Where are you currently based?",
    "tech_stack": "List your tech stack — languages, frameworks, and tools, separated by commas.",
}

VALIDATION_ERRORS = {
    "email": "That doesn't look like a valid email. Please provide one like `name@company.com`.",
    "phone": "Please provide a valid phone number (7–15 digits, with or without country code).",
    "years_experience": "Please enter a number (e.g., `3` or `0` for fresh graduates).",
}


class InterviewEngine:
    def __init__(self, session: InterviewSession):
        self.session = session

    async def process_message(self, user_message: str) -> tuple[InterviewSession, str]:
        """Main entrypoint. Returns (updated_session, assistant_reply)."""
        self.session.messages.append(Message(role="user", content=user_message))
        self.session.updated_at = datetime.utcnow()

        context = self._build_context()
        is_relevant = await llm_service.check_relevance(user_message, context)

        if not is_relevant:
            reply = self._irrelevant_response()
        elif self.session.stage == InterviewStage.INFO_GATHERING:
            reply = await self._handle_info_stage(user_message)
        elif self.session.stage == InterviewStage.TECHNICAL:
            reply = await self._handle_technical_stage(user_message)
        else:
            reply = "Your interview is already complete. Thank you!"

        self.session.messages.append(Message(role="assistant", content=reply))
        return self.session, reply

    # ── Stage 1: Info Gathering ──────────────────────────────────────

    async def _handle_info_stage(self, message: str) -> str:
        if self.session.confirmation_pending:
            return await self._handle_confirmation(message)
        return await self._handle_field_collection(message)

    async def _handle_field_collection(self, message: str) -> str:
        field = self.session.current_field
        raw_value = await llm_service.extract_field_value(message, field)
        validated = validate_field(field, raw_value)

        if validated is None:
            return VALIDATION_ERRORS.get(
                field,
                f"I couldn't parse that. Please provide your {field.replace('_', ' ')}."
            )

        setattr(self.session.candidate_data, field, validated)

        next_field = next(
            (f for f in FIELD_ORDER if getattr(self.session.candidate_data, f) is None),
            None
        )

        if next_field:
            self.session.current_field = next_field
            return FIELD_PROMPTS[next_field]
        else:
            self.session.confirmation_pending = True
            return self._build_confirmation_prompt()

    async def _handle_confirmation(self, message: str) -> str:
        prompt = f"""Candidate message after reviewing their details:
"{message}"

Fields: name, email, phone, years_experience, desired_position, location, tech_stack

Does the user want to UPDATE a field?
Return ONLY: {{"wants_update": true/false, "field": "field_name_or_null", "new_value": "value_or_null"}}"""

        try:
            result_text = await llm_service.generate_text(prompt)
            result_text = result_text.strip().removeprefix("```json").removesuffix("```").strip()
            result = json.loads(result_text)
        except Exception:
            result = {"wants_update": False}

        if result.get("wants_update") and result.get("field"):
            field = result["field"]
            validated = validate_field(field, result.get("new_value"))
            if validated is not None:
                setattr(self.session.candidate_data, field, validated)
                return (
                    f"Updated **{field.replace('_', ' ').title()}** to: {validated}\n\n"
                    "Anything else to change, or shall we move to the technical questions?"
                )
            return f"That doesn't look valid for {field}. Please try again."
        else:
            return await self._transition_to_technical()

    async def _transition_to_technical(self) -> str:
        self.session.stage = InterviewStage.TECHNICAL
        self.session.question_count = 1
        self.session.confirmation_pending = False

        question = await llm_service.generate_technical_question(
            self.session.candidate_data.tech_stack, 1
        )
        self.session.current_question = question

        return (
            "All set! Let's move to the technical section.\n\n"
            f"**Question 1 of 5:**\n\n{question}"
        )

    # ── Stage 2: Technical Interview ────────────────────────────────

    async def _handle_technical_stage(self, message: str) -> str:
        self.session.technical_qa.append(TechnicalQA(
            question_number=self.session.question_count,
            question=self.session.current_question or "",
            answer=message
        ))

        if self.session.question_count >= 5:
            return await self._conclude()

        self.session.question_count += 1
        question = await llm_service.generate_technical_question(
            self.session.candidate_data.tech_stack, self.session.question_count
        )
        self.session.current_question = question

        return (
            f"Thanks for your answer.\n\n"
            f"**Question {self.session.question_count} of 5:**\n\n{question}"
        )

    async def _conclude(self) -> str:
        self.session.stage = InterviewStage.COMPLETED
        name = self.session.candidate_data.name or "there"
        email = self.session.candidate_data.email or "the address you provided"
        return (
            f"**Interview complete, {name}!** 🎉\n\n"
            "**What happens next:**\n"
            "1. Our team reviews your responses within 2–3 business days\n"
            f"2. You'll hear from us at **{email}**\n"
            "3. Shortlisted candidates proceed to a live technical round\n\n"
            "_Your session has been securely saved._"
        )

    # ── Helpers ──────────────────────────────────────────────────────

    def _build_context(self) -> str:
        stage_map = {1: "info gathering", 2: "technical interview", 3: "completed"}
        ctx = f"stage={stage_map.get(self.session.stage, 'unknown')}"
        if self.session.stage == InterviewStage.INFO_GATHERING:
            ctx += f", collecting={self.session.current_field}"
        return ctx

    def _build_confirmation_prompt(self) -> str:
        d = self.session.candidate_data
        return (
            "Here's what I have:\n\n"
            f"- **Name:** {d.name}\n"
            f"- **Email:** {d.email}\n"
            f"- **Phone:** {d.phone}\n"
            f"- **Experience:** {d.years_experience} year(s)\n"
            f"- **Position:** {d.desired_position}\n"
            f"- **Location:** {d.location}\n"
            f"- **Tech Stack:** {d.tech_stack}\n\n"
            "Does this look correct? Say *'update email to new@example.com'* to change "
            "anything, or *'looks good'* to start the technical questions."
        )

    def _irrelevant_response(self) -> str:
        if self.session.stage == InterviewStage.INFO_GATHERING:
            if self.session.confirmation_pending:
                return "Say *'looks good'* to continue or ask to update a field."
            return f"Let's stay on track — I still need your **{self.session.current_field.replace('_', ' ')}**."
        return "Please answer the current interview question to continue."
