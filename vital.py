from pathlib import Path
import json
import re
from datetime import datetime

from flask import Flask, Response
import requests
from icalendar import Calendar

app = Flask(__name__)

# ============================================================================
# Configuration
# ============================================================================

# Original iCal source (Rapla link)
ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"

# The exclusion rules now live in a JSON file for more flexibility
EXCLUSION_RULES_FILE = Path(__file__).with_name("exclusion_rules.json")

# Real Madrid CF calendar from FotMob
FOTMOB_RMCF_ICAL_URL = "https://pub.fotmob.com/prod/pub/api/v2/calendar/team/8633.ics"

# ============================================================================
# Rapla Calendar Filtering
# ============================================================================

def normalize(text: str) -> str:
    """Normalize text for safer comparisons."""
    return " ".join(str(text).strip().lower().split())


def load_exclusion_rules(file_path: Path) -> dict:
    """Load exclusion rules from JSON file.

    Expected format:
    {
        "always_excluded": ["event1", "event2"],
        "exclude_all_between": [
            {
                "start_date": "2026-03-24",
                "end_date": "2026-03-26",
                "description": "Hide all events while away"
            }
        ],
        "time_based_exclusions": [
            {
                "events": ["event3", "event4"],
                "start_date": "2025-09-22",
                "end_date": "2025-12-21",
                "description": "Optional description"
            }
        ]
    }
    """
    default_rules = {
        "always_excluded": [],
        "exclude_all_between": [],
        "time_based_exclusions": [],
    }

    if not file_path.exists() or not file_path.is_file():
        return default_rules

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "always_excluded": data.get("always_excluded", []),
        "exclude_all_between": data.get("exclude_all_between", []),
        "time_based_exclusions": data.get("time_based_exclusions", []),
    }


def get_event_date(event):
    """Extract the date from an event component."""
    dtstart = event.get("dtstart")
    if dtstart:
        dt = dtstart.dt
        if isinstance(dt, datetime):
            return dt.date()
        return dt
    return None


def should_keep(event, rules: dict) -> bool:
    """Check if an event should be kept based on exclusion rules.

    Returns:
        True if event should be kept, False if it should be excluded.
    """
    summary = normalize(event.get("summary", ""))
    event_date = get_event_date(event)

    # Check always excluded events
    for excluded_title in rules.get("always_excluded", []):
        if normalize(excluded_title) == summary:
            return False

    if event_date:
        # Check full-date blackout periods (exclude ALL events in range)
        for rule in rules.get("exclude_all_between", []):
            start_date = datetime.strptime(rule["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(rule["end_date"], "%Y-%m-%d").date()

            if start_date <= event_date <= end_date:
                return False

        # Check time-based exclusions for specific event titles
        for rule in rules.get("time_based_exclusions", []):
            start_date = datetime.strptime(rule["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(rule["end_date"], "%Y-%m-%d").date()

            if start_date <= event_date <= end_date:
                for excluded_title in rule.get("events", []):
                    if normalize(excluded_title) == summary:
                        return False

    return True


# ============================================================================
# Flask Routes
# ============================================================================

@app.route("/TINF23B6.ics")
def filtered_ics():
    """Rapla calendar with filtering based on exclusion rules."""
    rules = load_exclusion_rules(EXCLUSION_RULES_FILE)

    r = requests.get(ICAL_URL, timeout=15, headers={"User-Agent": "vital/1.0"})
    r.raise_for_status()
    cal = Calendar.from_ical(r.text)

    # Build filtered calendar based on exclusion rules
    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)

    for component in cal.walk():
        if component.name == "VEVENT" and should_keep(component, rules):
            new_cal.add_component(component)

    return Response(new_cal.to_ical(), content_type="text/calendar")


@app.route("/RMCF.ics")
def rmcf_ics():
    """Real Madrid CF calendar with cleaned event titles (soccer emoji removed)."""
    r = requests.get(FOTMOB_RMCF_ICAL_URL, timeout=15, headers={"User-Agent": "vital/1.0"})
    r.raise_for_status()
    raw_text = r.content.decode("utf-8", errors="replace")

    # Remove soccer emoji in all forms (actual emoji ⚽ and mojibake â½ï¸)
    emoji_patterns = ["⚽️", "⚽", "â½ï¸", "â½", "\u26bd\ufe0f", "\u26bd"]
    for emoji in emoji_patterns:
        raw_text = raw_text.replace(f"{emoji} ", "")
        raw_text = raw_text.replace(emoji, "")

    # Targeted cleanup after SUMMARY: and DESCRIPTION: fields
    for field in ["SUMMARY", "DESCRIPTION"]:
        for emoji in ["â½ï¸", "â½", "⚽️", "⚽"]:
            raw_text = re.sub(f"({field}:){emoji}\\s*", r"\1", raw_text)

    # Parse cleaned text and rebuild calendar
    cal = Calendar.from_ical(raw_text)
    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)
    for component in cal.walk():
        if component.name == "VEVENT":
            new_cal.add_component(component)

    return Response(new_cal.to_ical(), content_type="text/calendar")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
