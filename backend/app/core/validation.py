import re


def validate_field(field_name: str, value) -> str | int | None:
    """Validate and normalize. Returns cleaned value or None if invalid."""
    if value is None:
        return None

    if field_name == "email":
        v = str(value).strip().lower()
        return v if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v) else None

    if field_name == "phone":
        digits = re.sub(r'\D', '', str(value))
        return digits if 7 <= len(digits) <= 15 else None

    if field_name == "years_experience":
        try:
            v = int(value)
            return v if v >= 0 else None
        except (TypeError, ValueError):
            return None

    v = str(value).strip()
    return v if len(v) >= 1 else None
