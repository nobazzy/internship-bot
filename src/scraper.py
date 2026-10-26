# internship_bot/src/scraper.py
"""Scraper utilities for the Internship Bot.

Currently the bot supports fetching vacancy listings from an RSS feed (e.g., Gupy).
Future extensions can add Selenium‑based page scraping for sites without RSS.
"""

import feedparser
from typing import List, Dict
import logging


def fetch_vacancies(rss_url: str) -> List[Dict]:
    """Fetch vacancy entries from the provided RSS URL.

    Parameters
    ----------
    rss_url: str
        URL of the RSS feed that returns job postings.

    Returns
    -------
    List[Dict]
        A list of dictionaries, each containing ``id``, ``title`` and ``link``.
    """
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        logging.error(f"Failed to parse RSS feed: {rss_url}\nError: {feed.bozo_exception}")
        return []

    vacancies = []
    for entry in feed.entries:
        # feedparser gives a unique ``id`` if present; fall back to link if missing.
        entry_id = getattr(entry, "id", entry.link)
        vacancies.append({
            "id": entry_id,
            "title": entry.title,
            "link": entry.link,
        })
    return vacancies
