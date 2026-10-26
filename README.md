# Internship Application Engine

Autonomous multi-platform job scraper and application engine engineered for LinkedIn Easy Apply, Gupy, and major regional career portals.

Designed to eliminate repetitive manual applications through structured RSS scraping, automated browser control with humanized interaction patterns, SQLite state persistence, and automated notifications.

---

## Architecture Overview

```
                                 [ Scheduled Trigger / CLI ]
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
            [ LinkedIn Scraper ]       [ Gupy RSS Engine ]     [ Portal Aggregator ]
                      │                       │                       │
                      └───────────────────────┼───────────────────────┘
                                              ▼
                                 [ SQLite Persistence Layer ]
                                 (Deduplication & State Flag)
                                              │
                                              ▼
                                 [ Selenium Runner Engine ]
                                 (Humanized Timing & Form Fill)
                                              │
                                 [ Notification Service ]
                                 (SMTP / Email Dispatch)
```

### Core Components

- **Multi-Source Scraping Engine**: Fetches opportunities from LinkedIn, Gupy, and aggregator feeds with customizable location, role, and publication date filters.
- **Deduplication & State Management**: Utilizes SQLite with unique index constraints to prevent duplicate applications and track processing status (`pending`, `applied`, `failed`).
- **Humanized Automation**: Implements randomized jitter delays, natural mouse movements, and resilient DOM selector fallbacks to ensure stable browser interactions.
- **Configurable Application Rules**: Modular YAML configuration defining candidate profile, targeted roles, geographic bounds, and platform credentials.

---

## Tech Stack

- **Language**: Python 3.10+
- **Browser Automation**: Selenium WebDriver, undetected-chromedriver
- **Data Persistence**: SQLite3
- **Configuration & Parsing**: PyYAML, BeautifulSoup4, Feedparser
- **Notifications**: Python SMTP / SSL

---

## Project Structure

```
internship_bot/
├── src/
│   ├── scraper.py          # Multi-platform vacancy discovery & RSS parsing
│   ├── apply.py            # Form automation and application workflows
│   ├── linkedin_bot.py     # LinkedIn Easy Apply flow automation
│   ├── db.py               # SQLite schema, queries, and state management
│   └── notifier.py         # Automated email and reporting dispatcher
├── config.example.yaml     # Configuration template
├── main.py                 # Core orchestration entrypoint
├── requirements.txt        # Python dependency manifest
└── README.md               # Project documentation
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- Google Chrome installed

### 2. Installation

Clone the repository and install required packages:

```bash
git clone https://github.com/nobazzy/internship-bot.git
cd internship-bot
pip install -r requirements.txt
```

### 3. Configuration

Copy the example configuration file and customize your settings:

```bash
cp config.example.yaml config.yaml
```

Update `config.yaml` with your target job titles, locations, and optional platform credentials.

### 4. Running the Engine

Execute the main pipeline:

```bash
python main.py
```

---

## Disclaimer

This project is developed for educational and personal workflow automation purposes. Use responsibly in compliance with the terms of service of each platform.
