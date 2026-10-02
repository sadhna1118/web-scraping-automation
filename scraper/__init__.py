"""
Web Scraper Module
"""

from scraper.parsers import (
    clean_text,
    scrape_headings,
    scrape_images,
    scrape_links,
    scrape_paragraphs,
    scrape_tables,
    scrape_title,
)
from scraper.scraper import ScrapeResult, WebScraper
from scraper.validators import check_robots_permission, sanitize_url, validate_url

__all__ = [
    "WebScraper",
    "ScrapeResult",
    "scrape_title",
    "scrape_headings",
    "scrape_links",
    "scrape_paragraphs",
    "scrape_tables",
    "scrape_images",
    "validate_url",
    "sanitize_url",
    "check_robots_permission",
    "clean_text",
]
