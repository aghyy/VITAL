from pathlib import Path
import json
from datetime import datetime

from flask import Flask, Response
import requests
from icalendar import Calendar

app = Flask(__name__)

# Original iCal source (Rapla link)
ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"

# The exclusion rules now live in a JSON file for more flexibility
EXCLUSION_RULES_FILE = Path(__file__).with_name("exclusion_rules.json")


def load_exclusion_rules(file_path: Path) -> dict:
    """Load exclusion rules from JSON file.
    
    Expected format:
    {
        "always_excluded": ["event1", "event2", ...],
        "time_based_exclusions": [
            {
                "events": ["event3", "event4", ...],
                "start_date": "2025-09-22",
                "end_date": "2025-12-21",
                "description": "Optional description"
            }
        ]
    }
    """
    if not file_path.exists():
        return {"always_excluded": [], "time_based_exclusions": []}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


EXCLUSION_RULES = load_exclusion_rules(EXCLUSION_RULES_FILE)


def get_event_date(event):
    """Extract the date from an event component."""
    dtstart = event.get('dtstart')
    if dtstart:
        dt = dtstart.dt
        # Handle both date and datetime objects
        if isinstance(dt, datetime):
            return dt.date()
        return dt
    return None


def should_keep(event):
    """Check if an event should be kept based on exclusion rules."""
    summary = str(event.get('summary', ''))
    
    # Check always excluded events
    for excluded_title in EXCLUSION_RULES.get('always_excluded', []):
        if excluded_title.lower() in summary.lower():
            return False
    
    # Check time-based exclusions
    event_date = get_event_date(event)
    if event_date:
        for rule in EXCLUSION_RULES.get('time_based_exclusions', []):
            start_date = datetime.strptime(rule['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(rule['end_date'], '%Y-%m-%d').date()
            
            # Check if event is within the date range
            if start_date <= event_date <= end_date:
                # Check if event matches any of the excluded titles for this period
                for excluded_title in rule['events']:
                    if excluded_title.lower() in summary.lower():
                        return False
    
    return True

@app.route("/TINF23B6.ics")
def filtered_ics():
    # Fetch original iCal
    r = requests.get(ICAL_URL)
    cal = Calendar.from_ical(r.text)

    # Build new filtered calendar
    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)
    for component in cal.walk():
        if component.name == "VEVENT" and should_keep(component):
            new_cal.add_component(component)

    return Response(new_cal.to_ical(), content_type="text/calendar")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)