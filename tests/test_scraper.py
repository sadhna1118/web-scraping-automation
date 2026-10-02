"""
Comprehensive Unit and Integration Tests for Web Scraping Automation Suite.
Tests validators, parsers, engine orchestrator, database CRUD, and export utilities.
"""

import os
import tempfile
from bs4 import BeautifulSoup
import pandas as pd
import pytest

from database.db import clear_history, get_history, get_stats, init_db, save_history
from scraper.parsers import (
    clean_text,
    scrape_headings,
    scrape_links,
    scrape_paragraphs,
    scrape_tables,
    scrape_title,
)
from scraper.scraper import WebScraper
from scraper.validators import sanitize_url, validate_url
from utils.export import export_to_csv, export_to_excel, export_to_json

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Test Page</title>
    <meta name="description" content="A test page for scraper verification.">
    <link rel="canonical" href="https://example.com/canonical-test">
</head>
<body>
    <h1>Main Header</h1>
    <h2>Sub Header 1</h2>
    <h2>Sub Header 2</h2>
    <h3>Section Detail</h3>

    <p>This is the first paragraph with some details.</p>
    <p>This is the second paragraph with more words and statistics.</p>
    <p>   </p> <!-- Empty paragraph to test filtering -->

    <a href="/internal-link">Internal Relative Link</a>
    <a href="https://other.com/external-link">External Link</a>
    <a href="/internal-link">Internal Relative Link</a> <!-- Duplicate -->
    <a href="#section">Jump Anchor (should be ignored)</a>

    <table id="test-table">
        <thead>
            <tr>
                <th>Item</th>
                <th>Price</th>
                <th>Qty</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Widget A</td>
                <td>$10</td>
                <td>5</td>
            </tr>
            <tr>
                <td>Widget B</td>
                <td>$20</td>
                <td>3</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
"""


# ---------------------------------------------------------
# 1. URL Validation & Sanitization Tests
# ---------------------------------------------------------

def test_url_sanitization():
    assert sanitize_url("  quotes.toscrape.com  ") == "https://quotes.toscrape.com"
    assert sanitize_url("http://example.com") == "http://example.com"
    assert sanitize_url("https://example.com/test") == "https://example.com/test"
    assert sanitize_url("") == ""


def test_url_validation_valid():
    is_valid, err = validate_url("https://quotes.toscrape.com")
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_url("http://books.toscrape.com/catalogue/page-1.html")
    assert is_valid is True
    assert err == ""


def test_url_validation_invalid():
    # Empty URL
    is_valid, err = validate_url("")
    assert is_valid is False
    assert "empty" in err.lower()

    # Unsupported protocol
    is_valid, err = validate_url("ftp://example.com")
    assert is_valid is False
    assert "protocol" in err.lower()

    # Missing domain
    is_valid, err = validate_url("https://")
    assert is_valid is False
    assert "domain" in err.lower() or "structure" in err.lower()


# ---------------------------------------------------------
# 2. Parsers Tests
# ---------------------------------------------------------

def test_scrape_title():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    df = scrape_title(soup, base_url="https://example.com")
    assert not df.empty
    assert df["Page Title"].iloc[0] == "Sample Test Page"
    assert df["Meta Description"].iloc[0] == "A test page for scraper verification."
    assert "canonical-test" in df["Canonical URL"].iloc[0]


def test_scrape_headings():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    df = scrape_headings(soup, base_url="https://example.com")
    assert len(df) == 4
    assert df["Tag"].tolist() == ["H1", "H2", "H2", "H3"]
    assert "Main Header" in df["Heading Text"].values


def test_scrape_links_and_normalization():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    df = scrape_links(soup, base_url="https://example.com")
    
    # Check that duplicates were removed and jump anchors skipped
    urls = df["URL"].tolist()
    assert "https://example.com/internal-link" in urls
    assert "https://other.com/external-link" in urls
    assert not any("#section" in u for u in urls)
    
    # Check link types
    internal_row = df[df["URL"] == "https://example.com/internal-link"].iloc[0]
    assert internal_row["Type"] == "Internal"

    external_row = df[df["URL"] == "https://other.com/external-link"].iloc[0]
    assert external_row["Type"] == "External"


def test_scrape_paragraphs():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    df = scrape_paragraphs(soup, base_url="https://example.com")
    # Empty paragraph should be filtered out
    assert len(df) == 2
    assert "first paragraph" in df["Paragraph Text"].iloc[0]
    assert df["Word Count"].iloc[0] > 0


def test_scrape_tables():
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    df = scrape_tables(soup, base_url="https://example.com")
    assert not df.empty
    assert list(df.columns) == ["Item", "Price", "Qty"]
    assert len(df) == 2
    assert df["Item"].iloc[0] == "Widget A"
    assert df["Price"].iloc[1] == "$20"


def test_clean_text():
    raw = "   Line 1 \n\n  \t  Line 2   "
    assert clean_text(raw) == "Line 1 Line 2"
    assert clean_text(None) == ""


# ---------------------------------------------------------
# 3. Scraper Engine In-Memory HTML Tests
# ---------------------------------------------------------

def test_engine_scrape_html():
    scraper = WebScraper()
    result = scraper.scrape_html(SAMPLE_HTML, scrape_type="Headings", base_url="https://example.com")
    assert result.success is True
    assert result.record_count == 4
    assert result.data is not None
    assert len(result.logs) > 0


def test_engine_invalid_type():
    scraper = WebScraper()
    result = scraper.scrape_html(SAMPLE_HTML, scrape_type="NonExistentType")
    assert result.success is False
    assert "Unknown scraping type" in (result.error_message or "")


# ---------------------------------------------------------
# 4. Database CRUD & Statistics Tests
# ---------------------------------------------------------

def test_database_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = os.path.join(tmp_dir, "test_history.db")
        init_db(test_db)

        # Test insert
        dummy_df = pd.DataFrame([{"col1": "A", "col2": "B"}])
        rec_id1 = save_history(
            url="https://quotes.toscrape.com",
            scrape_type="Headings",
            record_count=15,
            status="Success",
            execution_time=0.45,
            preview_df=dummy_df,
            db_path=test_db,
        )
        assert rec_id1 > 0

        rec_id2 = save_history(
            url="https://invalid-site.xyz",
            scrape_type="Links",
            record_count=0,
            status="Failed",
            execution_time=0.20,
            error_message="Connection timeout",
            db_path=test_db,
        )
        assert rec_id2 > 0

        # Test get history
        df_history = get_history(db_path=test_db)
        assert len(df_history) == 2

        # Test filter by search query
        df_search = get_history(search_query="quotes", db_path=test_db)
        assert len(df_search) == 1
        assert "quotes.toscrape.com" in df_search["Target URL"].iloc[0]

        # Test stats
        stats = get_stats(db_path=test_db)
        assert stats["total_scrapes"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["total_records"] == 15
        assert stats["success_rate"] == 50.0

        # Test clear history
        cleared = clear_history(test_db)
        assert cleared is True
        df_empty = get_history(db_path=test_db)
        assert len(df_empty) == 0


# ---------------------------------------------------------
# 5. Export Utilities Tests
# ---------------------------------------------------------

def test_export_utilities():
    df = pd.DataFrame({
        "Name": ["Alice", "Bob"],
        "Score": [95, 88]
    })

    # CSV with UTF-8 BOM
    csv_bytes = export_to_csv(df)
    assert len(csv_bytes) > 0
    assert csv_bytes.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM

    # Excel with OpenPyXL
    excel_bytes = export_to_excel(df, sheet_name="TestSheet")
    assert len(excel_bytes) > 0
    # Check valid zip/xlsx signature (PK\x03\x04)
    assert excel_bytes[:2] == b"PK"

    # JSON export
    json_bytes = export_to_json(df)
    assert b"Alice" in json_bytes
    assert b"Score" in json_bytes
