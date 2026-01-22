# VITAL - Calendar Event Filter

A Flask application that provides two calendar processing endpoints:
1. **Rapla Calendar Filtering** - Filters out unwanted events based on time-based exclusion rules
2. **Real Madrid CF Calendar** - Cleans up FotMob calendar by removing soccer emojis from event titles

---

## Rapla Calendar Configuration

Edit `exclusion_rules.json` to control which events are filtered out from your Rapla calendar. The file supports two types of exclusions:

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
- The filter looks for **exact matches** (e.g., "Klausur Web-Services (60 min)" will only match if you write the full title)
- An event is excluded if it matches **any** rule that applies to its date

## Available Endpoints

### 1. Rapla Calendar (Filtered)
`http://localhost:8000/TINF23B6.ics`

Fetches events from your Rapla calendar and filters them based on the exclusion rules in `exclusion_rules.json`.

### 2. Real Madrid CF Calendar (Cleaned)
`http://localhost:8000/RMCF.ics`

Fetches Real Madrid CF matches from FotMob and removes the soccer emoji (⚽) and any leading whitespace/punctuation from event titles for a cleaner calendar display.

## Running the App

```bash
python vital.py
```

The app will start on `http://localhost:8000`

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```
