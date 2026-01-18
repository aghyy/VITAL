# VITAL - Calendar Event Filter

A Flask application that filters iCal events based on configurable exclusion rules.

## How It Works

The app fetches your calendar from a Rapla iCal URL and filters out unwanted events based on rules defined in `exclusion_rules.json`.

## Configuring Event Exclusions

Edit `exclusion_rules.json` to control which events are filtered out. The file supports two types of exclusions:

### 1. Always Excluded Events

Events in the `always_excluded` array are filtered out regardless of date:

```json
{
  "always_excluded": [
    "Canceled Event",
    "Blocked Time"
  ]
}
```

### 2. Time-Based Exclusions

Events in `time_based_exclusions` are only filtered during specific date ranges:

```json
{
  "time_based_exclusions": [
    {
      "description": "Optional description of why these are excluded",
      "start_date": "2025-09-22",
      "end_date": "2025-12-21",
      "events": [
        "Wahlmodul Event 1",
        "Wahlmodul Event 2"
      ]
    }
  ]
}
```

You can add multiple time-based exclusion rules with different date ranges.

### Matching Rules

- Event matching is **case-insensitive**
- The filter looks for **partial matches** (e.g., "Klausur" will match "Klausur Web-Services (60 min)")
- An event is excluded if it matches **any** rule that applies to its date

## Running the App

```bash
python vital.py
```

The filtered calendar will be available at: `http://localhost:8000/TINF23B6.ics`

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```
