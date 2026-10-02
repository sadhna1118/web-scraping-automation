"""
HTML Parsers Module
Extracts structured data (Title, Headings, Links, Paragraphs, Tables, Images)
from BeautifulSoup parsed HTML documents into clean Pandas DataFrames.
"""

import re
from typing import Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pandas as pd


def clean_text(text: Optional[str]) -> str:
    """Strip redundant whitespace, line breaks, and tabs from text."""
    if not text:
        return ""
    # Collapse multiple whitespace characters into a single space
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


def scrape_title(soup: BeautifulSoup, base_url: str = "") -> pd.DataFrame:
    """
    Extract webpage title, meta description, and canonical URL.
    Returns a DataFrame with 1 record or empty if no metadata found.
    """
    title_tag = soup.find("title")
    title_text = clean_text(title_tag.get_text()) if title_tag else "No Title Found"

    # Meta description
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or \
                soup.find("meta", attrs={"property": re.compile(r"og:description", re.I)})
    if desc_tag and desc_tag.get("content"):
        meta_desc = clean_text(desc_tag.get("content"))

    # Canonical URL
    canonical_url = ""
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    if canonical_tag and canonical_tag.get("href"):
        canonical_url = urljoin(base_url, canonical_tag.get("href").strip())

    data = [{
        "Page Title": title_text,
        "Length (Chars)": len(title_text),
        "Meta Description": meta_desc if meta_desc else "N/A",
        "Canonical URL": canonical_url if canonical_url else "N/A"
    }]
    return pd.DataFrame(data)


def scrape_headings(soup: BeautifulSoup, base_url: str = "", max_records: Optional[int] = None) -> pd.DataFrame:
    """
    Extract all heading tags (H1 - H6) in order of appearance.
    Returns a DataFrame with ['Level', 'Tag', 'Heading Text', 'Character Count'].
    """
    headings = []
    heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    for tag in heading_tags:
        text = clean_text(tag.get_text())
        if not text:
            continue
        level = tag.name.upper()
        headings.append({
            "Level": f"Heading {level[1]}",
            "Tag": level,
            "Heading Text": text,
            "Character Count": len(text)
        })

    if not headings:
        return pd.DataFrame(columns=["Level", "Tag", "Heading Text", "Character Count"])

    df = pd.DataFrame(headings)
    # Deduplicate identical headings in succession or completely identical
    df = df.drop_duplicates(subset=["Tag", "Heading Text"]).reset_index(drop=True)

    if max_records and max_records > 0:
        df = df.head(max_records)

    return df


def scrape_links(soup: BeautifulSoup, base_url: str = "", max_records: Optional[int] = None) -> pd.DataFrame:
    """
    Extract all anchor links with normalized absolute URLs.
    Classifies links as 'Internal' or 'External'.
    Returns a DataFrame with ['Text', 'URL', 'Type', 'Target'].
    """
    links = []
    base_domain = urlparse(base_url).netloc.lower() if base_url else ""

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        absolute_url = urljoin(base_url, href) if base_url else href
        text = clean_text(a_tag.get_text())
        if not text:
            text = "[No Text / Image / Icon]"

        link_domain = urlparse(absolute_url).netloc.lower()
        link_type = "Internal" if (not link_domain or link_domain == base_domain) else "External"
        target = a_tag.get("target", "_self")

        links.append({
            "Text": text,
            "URL": absolute_url,
            "Type": link_type,
            "Target": target
        })

    if not links:
        return pd.DataFrame(columns=["Text", "URL", "Type", "Target"])

    df = pd.DataFrame(links)
    # Deduplicate by URL + Text
    df = df.drop_duplicates(subset=["URL", "Text"]).reset_index(drop=True)

    if max_records and max_records > 0:
        df = df.head(max_records)

    return df


def scrape_paragraphs(soup: BeautifulSoup, base_url: str = "", max_records: Optional[int] = None) -> pd.DataFrame:
    """
    Extract all non-empty <p> tags with text statistics.
    Returns a DataFrame with ['Paragraph #', 'Paragraph Text', 'Word Count', 'Character Count'].
    """
    paragraphs = []
    for idx, p_tag in enumerate(soup.find_all("p"), start=1):
        text = clean_text(p_tag.get_text())
        if not text or len(text) < 3:  # Filter out trivial artifacts
            continue

        words = text.split()
        paragraphs.append({
            "Paragraph #": idx,
            "Paragraph Text": text,
            "Word Count": len(words),
            "Character Count": len(text)
        })

    if not paragraphs:
        return pd.DataFrame(columns=["Paragraph #", "Paragraph Text", "Word Count", "Character Count"])

    df = pd.DataFrame(paragraphs)
    # Deduplicate identical paragraphs
    df = df.drop_duplicates(subset=["Paragraph Text"]).reset_index(drop=True)
    df["Paragraph #"] = range(1, len(df) + 1)

    if max_records and max_records > 0:
        df = df.head(max_records)

    return df


def scrape_tables(soup: BeautifulSoup, base_url: str = "", max_records: Optional[int] = None) -> pd.DataFrame:
    """
    Parse HTML <table> elements into structured DataFrames.
    If multiple tables exist, consolidates them with a 'Table #' indicator.
    """
    tables = soup.find_all("table")
    if not tables:
        return pd.DataFrame()

    all_dfs = []
    for table_idx, table in enumerate(tables, start=1):
        # Extract headers from <thead> or first <tr>
        headers = []
        thead = table.find("thead")
        if thead:
            th_tags = thead.find_all(["th", "td"])
            headers = [clean_text(th.get_text()) for th in th_tags]

        # Extract rows
        rows_data = []
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue

            # If headers were not in <thead>, check if first row is all <th>
            if not headers and all(cell.name == "th" for cell in cells):
                headers = [clean_text(cell.get_text()) for cell in cells]
                continue

            row = [clean_text(cell.get_text()) for cell in cells]
            if any(row):  # Not completely empty
                rows_data.append(row)

        if not rows_data:
            continue

        # Determine column names
        max_cols = max(len(r) for r in rows_data)
        if not headers or len(headers) != max_cols:
            headers = [f"Column {i + 1}" for i in range(max_cols)]
        else:
            # Ensure header uniqueness
            seen = {}
            unique_headers = []
            for h in headers:
                name = h if h else "Column"
                count = seen.get(name, 0)
                seen[name] = count + 1
                unique_headers.append(f"{name}_{count}" if count > 0 else name)
            headers = unique_headers

        # Pad rows if some have fewer cells
        padded_rows = [r + [""] * (max_cols - len(r)) for r in rows_data]

        t_df = pd.DataFrame(padded_rows, columns=headers)
        if len(tables) > 1:
            t_df.insert(0, "Table #", f"Table {table_idx}")
        all_dfs.append(t_df)

    if not all_dfs:
        return pd.DataFrame()

    combined_df = pd.concat(all_dfs, ignore_index=True)
    if max_records and max_records > 0:
        combined_df = combined_df.head(max_records)

    return combined_df


def scrape_images(soup: BeautifulSoup, base_url: str = "", max_records: Optional[int] = None) -> pd.DataFrame:
    """
    Extract image tags (<img>) with Alt text and normalized URLs.
    Returns a DataFrame with ['Alt Text', 'Image URL', 'Type'].
    """
    images = []
    base_domain = urlparse(base_url).netloc.lower() if base_url else ""

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        src = src.strip()
        if not src or src.startswith("data:image"):
            continue

        absolute_src = urljoin(base_url, src) if base_url else src
        alt = clean_text(img.get("alt", "")) or "[No Alt Text]"
        img_domain = urlparse(absolute_src).netloc.lower()
        img_type = "Internal" if (not img_domain or img_domain == base_domain) else "External"

        images.append({
            "Alt Text": alt,
            "Image URL": absolute_src,
            "Type": img_type
        })

    if not images:
        return pd.DataFrame(columns=["Alt Text", "Image URL", "Type"])

    df = pd.DataFrame(images).drop_duplicates(subset=["Image URL"]).reset_index(drop=True)
    if max_records and max_records > 0:
        df = df.head(max_records)
    return df
