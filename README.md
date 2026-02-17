# VITAL - Calendar Event Filter

A Flask-based iCalendar proxy that provides two specialized calendar processing endpoints:

1. **Rapla Calendar Filtering** - Filter out unwanted events from your Rapla calendar based on flexible time-based rules
2. **Real Madrid CF Calendar Cleaning** - Clean up FotMob calendar by removing visual clutter (soccer emojis)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Available Endpoints](#available-endpoints)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Deployment](#deployment)

---

## Features

### Rapla Calendar Filtering
- **Time-based exclusions** - Hide events only during specific date ranges
- **Permanent exclusions** - Always hide certain events
- **Case-insensitive matching** - Works with any capitalization
- **Exact title matching** - Precise control over which events to exclude
- **Multiple date ranges** - Define different exclusion periods for different events

### Real Madrid CF Calendar Cleaning
- **Emoji removal** - Strips soccer emoji (⚽) from event titles
- **Encoding-safe** - Handles both UTF-8 and mojibake encodings
- **Complete cleanup** - Removes emoji from summaries, descriptions, and alarms
- **Zero configuration** - Works out of the box

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

   ```bash
   cd VITAL
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your exclusion rules file** (for Rapla filtering)

   Copy the example configuration:
   ```bash
   cp exclusion_rules.json.example exclusion_rules.json
   ```
   
   Or create `exclusion_rules.json` manually:
   ```json
   {
     "always_excluded": [],
     "time_based_exclusions": []
   }
   ```

5. **Run the application**

   ```bash
   python vital.py
   ```

   The server will start on `http://localhost:8000`

---

## Available Endpoints

### 1. Rapla Calendar (Filtered)

**Endpoint:** `http://localhost:8000/TINF23B6.ics`

**Purpose:** Fetches events from your Rapla calendar and filters them based on the exclusion rules defined in `exclusion_rules.json`.

**Use Case:** Hide optional modules, exam weeks, or other events during specific time periods (e.g., during internships or study abroad).

**Configuration:** Requires `exclusion_rules.json` - see [Configuration](#configuration) section below.

### 2. Real Madrid CF Calendar (Cleaned)

**Endpoint:** `http://localhost:8000/RMCF.ics`

**Purpose:** Fetches Real Madrid CF match fixtures from FotMob and removes the soccer emoji (⚽) from all event titles, descriptions, and alarms.

**Use Case:** Get a clean, professional-looking calendar of Real Madrid matches without emoji clutter.

**Configuration:** None required - works automatically.

---

## Configuration

### Rapla Calendar Exclusion Rules

Edit the `exclusion_rules.json` file to control which events are filtered from your Rapla calendar.

#### File Structure

```json
{
  "always_excluded": [
    "Event Title 1",
    "Event Title 2"
  ],
  "time_based_exclusions": [
    {
      "description": "Optional description for documentation",
      "start_date": "2025-09-22",
      "end_date": "2025-12-21",
      "events": [
        "Event Title 3",
        "Event Title 4"
      ]
    }
  ]
}
```

#### Configuration Options

##### 1. Always Excluded Events

Events listed in the `always_excluded` array are filtered out permanently, regardless of date.

**Example:**
```json
{
  "always_excluded": [
    "Canceled Course",
    "Optional Workshop"
  ]
}
```

**When to use:** Events you never want to see in your calendar.

##### 2. Time-Based Exclusions

Events listed in `time_based_exclusions` are only filtered during the specified date range.

**Example:**
```json
{
  "time_based_exclusions": [
    {
      "description": "Hide electives during internship semester",
      "start_date": "2025-09-22",
      "end_date": "2025-12-21",
      "events": [
        "Mathematische Grundlagen der Kryptographie",
        "Web-Services (WM-A)",
        "Klausur Wahlmodul 2aus4  (120 min)"
      ]
    },
    {
      "description": "Hide summer events during winter break",
      "start_date": "2025-12-22",
      "end_date": "2026-01-10",
      "events": [
        "Summer Project Kickoff"
      ]
    }
  ]
}
```

**When to use:** Events you want to hide only during specific periods (internships, study abroad, vacations).

#### Matching Rules

- **Case-insensitive:** "Klausur" matches "klausur" and "KLAUSUR"
- **Exact match:** Must match the complete event title
  - ✅ "Klausur Web-Services (60 min)" matches "Klausur Web-Services (60 min)"
  - ❌ "Klausur" does NOT match "Klausur Web-Services (60 min)"
- **Date range:** Inclusive on both start and end dates
- **Multiple rules:** An event is excluded if it matches ANY applicable rule

#### Tips

1. **Get exact event titles:** Subscribe to the original Rapla calendar, open an event, and copy its exact title
2. **Use descriptions:** Add `"description"` fields to document why certain events are excluded
3. **Multiple periods:** You can define as many time-based exclusion periods as needed
4. **Git-friendly:** The `.gitignore` already excludes `exclusion_rules.json` to keep your personal config private

---

## Usage Examples

### Example 1: Subscribe in Calendar App

Most calendar applications support subscribing to iCalendar URLs.

**Apple Calendar:**
1. File → New Calendar Subscription
2. Enter: `http://localhost:8000/TINF23B6.ics`
3. Set refresh interval (e.g., every hour)

**Google Calendar:**
1. Settings → Add calendar → From URL
2. Enter: `http://localhost:8000/TINF23B6.ics`
3. Google will auto-refresh periodically

**Outlook:**
1. Calendar → Add Calendar → Subscribe from web
2. Enter: `http://localhost:8000/TINF23B6.ics`

### Example 2: Configure Real Madrid Matches

```bash
# Start the server
python vital.py

# In your calendar app, subscribe to:
http://localhost:8000/RMCF.ics
```

All Real Madrid match events will appear without the soccer emoji prefix.

### Example 3: Multiple Exclusion Periods

```json
{
  "always_excluded": [],
  "time_based_exclusions": [
    {
      "description": "Hide electives during Fall internship",
      "start_date": "2025-09-01",
      "end_date": "2025-12-31",
      "events": [
        "Wahlmodul Course 1",
        "Wahlmodul Course 2"
      ]
    },
    {
      "description": "Hide electives during Spring internship",
      "start_date": "2026-03-01",
      "end_date": "2026-06-30",
      "events": [
        "Wahlmodul Course 3",
        "Wahlmodul Course 4"
      ]
    }
  ]
}
```

---

## Deployment

### Local Development

```bash
python vital.py
```

Access at `http://localhost:8000`

### Production with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 vital:app
```

- `-w 4` - Run with 4 worker processes
- `-b 0.0.0.0:8000` - Bind to all interfaces on port 8000

### Docker Deployment (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vital.py .
COPY exclusion_rules.json .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "vital:app"]
```

Build and run:

```bash
docker build -t vital .
docker run -p 8000:8000 -v $(pwd)/exclusion_rules.json:/app/exclusion_rules.json vital
```

### Environment Variables

You can customize URLs by editing the constants in `vital.py`:

```python
ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"
FOTMOB_RMCF_ICAL_URL = "https://pub.fotmob.com/prod/pub/api/v2/calendar/team/8633.ics"
```

---

## Dependencies

- **Flask** - Web framework for serving the iCalendar endpoints
- **icalendar** - Library for parsing and generating iCalendar files
- **requests** - HTTP library for fetching remote calendars
- **gunicorn** - Production WSGI server

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

## Project Structure

```
VITAL/
├── vital.py                  # Main Flask application
├── exclusion_rules.json      # Your personal exclusion configuration (gitignored)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore rules
└── .venv/                   # Virtual environment (gitignored)
```

---

## Troubleshooting

### Calendar app shows "Unable to subscribe"

**Solution:** Make sure the Flask server is running and accessible from your device.

For remote access (e.g., subscribing from your phone):
- Replace `localhost` with your computer's IP address
- Ensure port 8000 is not blocked by firewall
- Example: `http://192.168.1.100:8000/TINF23B6.ics`

### Events not being filtered

**Check:**
1. Is `exclusion_rules.json` formatted correctly? (valid JSON)
2. Are the event titles **exactly** matching (copy from original calendar)?
3. Are the dates in `YYYY-MM-DD` format?
4. Is the event date within the start/end date range?

**Debug tip:** Remove all exclusions and add them back one by one.

### Real Madrid calendar still shows emojis

**Solution:** The emoji removal happens server-side. Make sure:
1. You're accessing the VITAL endpoint, not the original FotMob URL
2. Your calendar app has refreshed (force refresh or wait for auto-refresh)
3. Try removing and re-adding the subscription

### Changes to exclusion_rules.json not taking effect

**Solution:** Restart the Flask server:
```bash
# Stop with Ctrl+C, then restart:
python vital.py
```

---

## License

This is a personal utility project. Feel free to use and modify as needed.

---

## Contributing

This is a personal project, but improvements are welcome! Feel free to:
- Report issues
- Suggest features
- Submit pull requests

---

## Credits

- Calendar data sources: Rapla (DHBW Karlsruhe) and FotMob
- Built with Flask and icalendar Python libraries
