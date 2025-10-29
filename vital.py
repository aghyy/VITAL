from flask import Flask, Response
import requests
from icalendar import Calendar

app = Flask(__name__)

# Original iCal source (Rapla link)
ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"

EXCLUDED_EVENTS = [
  "Mathematische Grundlagen der Kryptographie",
  "Ethik für Informatiker (WM-A)",
  "Gamification",
  "Supervised Machine Learning",
  "Digitale Forensik  (WMA)",
  "Web-Services (WM-A)",
  "Evolutionäre Algorithmen",
  "Studienarbeit",
  "Bildverarbetiung  (BV & CG)",
  "Interaktive Systeme (KI & IS)",
  ".Grundlagen der KI (KI & BV)",
  "Kommunikations und Netztechnik II",
  "Interaktive Systeme (KI & IS)",
  "Computergraphik  (BV & CG)",
  "Bildverarbeitung (KI & BV)",
  "Allerheiligen",
  "Netzwerktreffen für Studentinnen",
  "Grundlagen der KI (KI & IS)",
]

# Define what to keep/remove
def should_keep(event):
    summary = str(event.get('summary', '')).lower()
    # Edit this logic to filter what you don't want to keep
    if any(word.lower() in summary for word in EXCLUDED_EVENTS):
        return False
    return True

@app.route("/vital.ics")
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