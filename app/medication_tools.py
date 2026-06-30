# This tool implements the Day 3 Agent Skills & Memory concept.
# It allows the agent to maintain local memory of medication schedules and symptom history across turns.

import sqlite3
import os
import datetime
from zoneinfo import ZoneInfo

# Setup DB path relative to the project root directory
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "mediguide.db")


def init_db() -> None:
    """Initializes the SQLite database and creates the required tables if they do not exist.
    
    This function creates the 'medications' table for managing medication schedules
    and the 'symptom_logs' table for recording user-reported symptoms.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            drug_name TEXT,
            dosage TEXT,
            frequency TEXT,
            time_of_day TEXT,
            notes TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symptom_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            symptom TEXT,
            severity INTEGER,
            notes TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_medication(
    user_id: str,
    drug_name: str,
    dosage: str,
    frequency: str,
    time_of_day: str,
    notes: str
) -> str:
    """Adds a new medication to the user's schedule.

    Args:
        user_id: Unique identifier for the user.
        drug_name: The name of the medication.
        dosage: The quantity and form of the medication (e.g., 500mg).
        frequency: How often the medication should be taken (e.g., daily, weekly).
        time_of_day: Specific time or times of day (e.g., Morning, 8:00 AM).
        notes: Additional instructions or information about the medication.

    Returns:
        A confirmation message indicating success.
    """
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO medications (user_id, drug_name, dosage, frequency, time_of_day, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, drug_name, dosage, frequency, time_of_day, notes, created_at)
    )
    conn.commit()
    conn.close()
    return f"Successfully added {drug_name} to your medication schedule."


def get_medications(user_id: str) -> str:
    """Retrieves all registered medications for a specific user.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        A formatted string list of all medications for the user, or "No medications found."
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT drug_name, dosage, frequency, time_of_day, notes FROM medications
        WHERE user_id = ?
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No medications found."

    lines = []
    for row in rows:
        drug_name, dosage, frequency, time_of_day, notes = row
        note_str = f" (Notes: {notes})" if notes else ""
        lines.append(f"- {drug_name}: {dosage}, {frequency}, {time_of_day}{note_str}")
    return "\n".join(lines)


def get_todays_schedule(user_id: str) -> str:
    """Retrieves the medication schedule for today formatted as a checklist.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        A formatted string checklist of medications due today, or "No medications scheduled for today."
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT drug_name, dosage, frequency, time_of_day, notes, created_at FROM medications
        WHERE user_id = ?
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No medications scheduled for today."

    now = datetime.datetime.now(datetime.timezone.utc)
    today_weekday = now.weekday()

    due_meds = []
    for row in rows:
        drug_name, dosage, frequency, time_of_day, notes, created_at_str = row
        is_due = True

        freq_lower = frequency.lower()
        if "weekly" in freq_lower:
            try:
                created_dt = datetime.datetime.fromisoformat(created_at_str)
                if created_dt.weekday() != today_weekday:
                    is_due = False
            except Exception:
                pass

        if is_due:
            note_str = f" ({notes})" if notes else ""
            due_meds.append(f"[ ] {drug_name} - {dosage} ({time_of_day}){note_str}")

    if not due_meds:
        return "No medications scheduled for today."

    return "\n".join(due_meds)


def log_symptom(user_id: str, symptom: str, severity: int, notes: str) -> str:
    """Logs a symptom occurrence for a user.

    Args:
        user_id: Unique identifier for the user.
        symptom: The name or description of the symptom (e.g., headache).
        severity: An integer representing severity (e.g., 1 to 10).
        notes: Additional context or comments about the symptom.

    Returns:
        A confirmation message indicating success.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO symptom_logs (user_id, symptom, severity, notes, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, symptom, severity, notes, timestamp)
    )
    conn.commit()
    conn.close()
    return "Symptom logged successfully."


def get_symptom_history(user_id: str) -> str:
    """Retrieves a summary of the symptoms logged by the user in the last 7 days.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        A formatted string summary of symptom history over the last 7 days.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT symptom, severity, notes, timestamp FROM symptom_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No symptoms logged in the last 7 days."

    now = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago = now - datetime.timedelta(days=7)

    recent_logs = []
    for row in rows:
        symptom, severity, notes, timestamp_str = row
        try:
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            if timestamp >= seven_days_ago:
                date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                note_str = f" - Notes: {notes}" if notes else ""
                recent_logs.append(f"- [{date_str}] {symptom} (Severity: {severity}/10){note_str}")
        except Exception:
            pass

    if not recent_logs:
        return "No symptoms logged in the last 7 days."

    return "\n".join(recent_logs)


# Call init_db() at module level so DB is ready on import
init_db()
