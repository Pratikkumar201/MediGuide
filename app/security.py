import os
import datetime
import re

# Resolve logs directory path relative to project root
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def sanitize_input(user_input: str) -> str:
    """Strips common prompt injection patterns from user input.

    Args:
        user_input: The raw user input string.

    Returns:
        The sanitized user input string with injection patterns removed.
    """
    patterns = [
        r"ignore\s+previous\s+instructions",
        r"you\s+are\s+now",
        r"forget\s+everything",
        r"disregard",
        r"new\s+persona",
        r"act\s+as",
        r"jailbreak"
    ]
    
    cleaned = user_input
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    
    return cleaned


def is_medical_query(user_input: str) -> bool:
    """Checks if the user's input is health or medication related.

    Returns True when the input contains any recognised medical keyword, OR
    when the message is short (< 15 words) — short messages are almost always
    follow-up questions that should be allowed through without keyword matching.
    Only long, clearly non-medical messages are refused.

    Args:
        user_input: The input string from the user.

    Returns:
        True if the input is likely health/medication related; False otherwise.
    """
    # Short messages pass through — likely follow-ups or quick commands
    if len(user_input.split()) < 15:
        return True

    medical_terms = [
        # Core medication vocabulary
        "drug", "medicine", "medication", "pill", "tablet", "capsule",
        "dosage", "dose", "interaction", "side effect", "symptom",
        "prescription", "pharmacy", "health", "pain", "fever", "headache",
        "antibiotic", "vitamin", "supplement",
        # Common drug names
        "paracetamol", "ibuprofen", "aspirin", "metformin", "amoxicillin",
        # Scheduling / action verbs
        "add", "schedule", "take", "taking", "took",
        "morning", "evening", "night", "afternoon",
        "log", "track", "feeling",
        # Symptoms
        "nausea", "nauseous", "dizzy", "dizziness", "tired", "fatigue",
        # Dosage units & forms
        "mg", "ml", "twice", "once", "daily", "weekly",
        "drop", "spray", "inhaler",
        # Healthcare roles
        "doctor", "pharmacist",
        # Conditions / reactions
        "allergy", "allergic", "reaction", "blood pressure",
        "diabetes", "infection", "inflammation", "cold", "flu",
        "cough", "chest", "stomach", "back",
        "anxiety", "depression", "sleep", "insomnia",
        "heart", "kidney", "liver",
    ]

    input_lower = user_input.lower()
    return any(term in input_lower for term in medical_terms)


def log_action(agent_name: str, action_preview: str) -> None:
    """Logs agent actions to logs/audit.log with a timestamp.

    Args:
        agent_name: The identifier of the agent performing the action.
        action_preview: A preview string summarizing the action.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    audit_log_path = os.path.join(LOGS_DIR, "audit.log")
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    action_truncated = action_preview[:80]
    
    log_line = f"[{timestamp}] [{agent_name}] {action_truncated}\n"
    
    with open(audit_log_path, "a", encoding="utf-8") as f:
        f.write(log_line)
