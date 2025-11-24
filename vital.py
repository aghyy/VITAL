from pathlib import Path

from flask import Flask, Response
import requests
from icalendar import Calendar

app = Flask(__name__)

# Original iCal source (Rapla link)
ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"

# The list of excluded event titles now lives in a sidecar file so non-devs can
# adjust it without touching the code. Each non-empty line becomes one entry.
EXCLUDED_EVENTS_FILE = Path(__file__).with_name("excluded_events.txt")


def load_excluded_events(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []
    return [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


EXCLUDED_EVENTS = load_excluded_events(EXCLUDED_EVENTS_FILE)

# Define what to keep/remove
def should_keep(event):
    summary = str(event.get('summary', '')).lower()
    # Edit this logic to filter what you don't want to keep
    if any(word.lower() in summary for word in EXCLUDED_EVENTS):
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