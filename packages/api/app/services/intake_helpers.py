"""Helper functions for intake record processing."""

from app.models.intake import IntakeRecord


def get_missing_fields(intake_record: IntakeRecord) -> list[str]:
    """
    Identify which required fields are missing.

    Uses dynamic field checking to avoid duplication with IntakeRecord.is_complete().

    Args:
        intake_record: IntakeRecord to check

    Returns:
        List of missing field names
    """
    required_fields = ["location", "service_type", "outcome"]
    return [
        field for field in required_fields
        if getattr(intake_record, field) is None
    ]


def generate_followup_question(missing_fields: list[str]) -> str:
    """
    Generate contextual follow-up question for missing fields.

    Args:
        missing_fields: List of missing field names

    Returns:
        Follow-up question text
    """
    if not missing_fields:
        return (
            "Thank you! I have all the information I need. "
            "Your service report has been recorded."
        )

    # Prioritize fields and ask about the most important one
    field_questions = {
        "location": (
            "Where did you perform this service call? "
            "Please provide the address or location."
        ),
        "service_type": (
            "What type of service did you perform? "
            "(e.g., HVAC, Plumbing, Electrical)"
        ),
        "outcome": (
            "What was the outcome of the service call? "
            "(e.g., completed, needs_followup, escalated)"
        ),
    }

    # Ask about first missing field
    first_missing = missing_fields[0]
    return field_questions.get(first_missing, f"Could you provide the {first_missing}?")
