from pathlib import Path
import json
import re
from datetime import datetime, date, timedelta

from flask import Flask, Response
import requests
from icalendar import Calendar, vDDDLists
from dateutil.rrule import rrulestr

app = Flask(__name__)

# ============================================================================
# Configuration
# ============================================================================

ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"
EXCLUSION_RULES_FILE = Path(__file__).with_name("exclusion_rules.json")
FOTMOB_RMCF_ICAL_URL = "https://pub.fotmob.com/prod/pub/api/v2/calendar/team/8633.ics"

# ============================================================================
# Helpers
# ============================================================================

def normalize(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def load_exclusion_rules(file_path: Path) -> dict:
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
    dtstart = event.get("dtstart")
    if dtstart:
        dt = dtstart.dt
        if isinstance(dt, datetime):
            return dt.date()
        return dt
    return None


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def get_blackout_ranges(rules: dict) -> list[tuple[date, date]]:
    ranges = []
    for rule in rules.get("exclude_all_between", []):
        ranges.append((parse_date(rule["start_date"]), parse_date(rule["end_date"])))
    return ranges


def date_in_any_range(day: date, ranges: list[tuple[date, date]]) -> bool:
    return any(start <= day <= end for start, end in ranges)


def title_excluded_for_date(summary: str, event_date: date | None, rules: dict) -> bool:
    normalized_summary = normalize(summary)

    for excluded_title in rules.get("always_excluded", []):
        if normalize(excluded_title) == normalized_summary:
            return True

    if event_date:
        for rule in rules.get("time_based_exclusions", []):
            start_date = parse_date(rule["start_date"])
            end_date = parse_date(rule["end_date"])

            if start_date <= event_date <= end_date:
                for excluded_title in rule.get("events", []):
                    if normalize(excluded_title) == normalized_summary:
                        return True

    return False


def expand_recurring_occurrences(event, window_start: date, window_end: date) -> list[datetime]:
    """
    Expand recurring occurrences only within the relevant blackout window.
    """
    dtstart_prop = event.get("dtstart")
    rrule_prop = event.get("rrule")

    if not dtstart_prop or not rrule_prop:
        return []

    dtstart = dtstart_prop.dt
    if not isinstance(dtstart, datetime):
        return []

    rrule_lines = []
    for key, value in rrule_prop.items():
        if isinstance(value, list):
            joined = ",".join(str(v) for v in value)
        else:
            joined = str(value)
        rrule_lines.append(f"{key}={joined}")

    rule_string = "RRULE:" + ";".join(rrule_lines)

    rule = rrulestr(rule_string, dtstart=dtstart)

    window_start_dt = datetime.combine(window_start, datetime.min.time(), tzinfo=dtstart.tzinfo)
    window_end_dt = datetime.combine(window_end + timedelta(days=1), datetime.min.time(), tzinfo=dtstart.tzinfo)

    occurrences = rule.between(window_start_dt, window_end_dt, inc=True)
    return occurrences


def add_exdates(event, datetimes_to_exclude: list[datetime]) -> None:
    if not datetimes_to_exclude:
        return

    existing = event.get("exdate")
    if existing is None:
        event.add("exdate", datetimes_to_exclude)
        return

    existing_dates = []
    if isinstance(existing, list):
        for item in existing:
            if hasattr(item, "dts"):
                existing_dates.extend([x.dt for x in item.dts])
    elif hasattr(existing, "dts"):
        existing_dates.extend([x.dt for x in existing.dts])

    merged = []
    seen = set()

    for dt in existing_dates + datetimes_to_exclude:
        key = dt.isoformat()
        if key not in seen:
            seen.add(key)
            merged.append(dt)

    event.pop("exdate")
    event.add("exdate", merged)


def filter_event(component, rules: dict):
    """
    Returns:
      - None if event should be removed completely
      - event component (possibly modified with EXDATEs) if it should be kept
    """
    summary = str(component.get("summary", ""))
    event_date = get_event_date(component)

    # Title-based exclusions for one-off / master event date
    if title_excluded_for_date(summary, event_date, rules):
        return None

    blackout_ranges = get_blackout_ranges(rules)
    if not blackout_ranges:
        return component

    # Non-recurring event: remove if its date falls in a blackout range
    if component.get("rrule") is None:
        if event_date and date_in_any_range(event_date, blackout_ranges):
            return None
        return component

    # Recurring event:
    # Add EXDATEs for all occurrences inside blackout ranges
    to_exclude = []
    for start_date, end_date in blackout_ranges:
        occurrences = expand_recurring_occurrences(component, start_date, end_date)
        for occ in occurrences:
            if start_date <= occ.date() <= end_date:
                to_exclude.append(occ)

    if to_exclude:
        add_exdates(component, to_exclude)

    return component


# ============================================================================
# Flask Routes
# ============================================================================

@app.route("/TINF23B6.ics")
def filtered_ics():
    rules = load_exclusion_rules(EXCLUSION_RULES_FILE)

    r = requests.get(ICAL_URL, timeout=15, headers={"User-Agent": "vital/1.0"})
    r.raise_for_status()
    cal = Calendar.from_ical(r.text)

    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)

    for component in cal.walk():
        if component.name == "VEVENT":
            filtered = filter_event(component, rules)
            if filtered is not None:
                new_cal.add_component(filtered)

    return Response(new_cal.to_ical(), content_type="text/calendar")


@app.route("/RMCF.ics")
def rmcf_ics():
    r = requests.get(FOTMOB_RMCF_ICAL_URL, timeout=15, headers={"User-Agent": "vital/1.0"})
    r.raise_for_status()
    raw_text = r.content.decode("utf-8", errors="replace")

    emoji_patterns = ["⚽️", "⚽", "â½ï¸", "â½", "\u26bd\ufe0f", "\u26bd"]
    for emoji in emoji_patterns:
        raw_text = raw_text.replace(f"{emoji} ", "")
        raw_text = raw_text.replace(emoji, "")

    for field in ["SUMMARY", "DESCRIPTION"]:
        for emoji in ["â½ï¸", "â½", "⚽️", "⚽"]:
            raw_text = re.sub(f"({field}:){emoji}\\s*", r"\1", raw_text)

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
