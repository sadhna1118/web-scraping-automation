"""
Scraping Engine Module
Core orchestration for HTTP fetching, validation, parsing, error handling, and performance logging.
"""

from dataclasses import dataclass, field
import logging
import time
from typing import List, Optional
from bs4 import BeautifulSoup
import pandas as pd
import requests

from scraper.parsers import (
    scrape_headings,
    scrape_images,
    scrape_links,
    scrape_paragraphs,
    scrape_tables,
    scrape_title,
)
from scraper.validators import check_robots_permission, sanitize_url, validate_url

logger = logging.getLogger("scraper")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 (WebScrapingAutomation/1.0)"
)


@dataclass
class ScrapeResult:
    """Standardized result object returned by the scraper engine."""
    success: bool
    url: str
    scrape_type: str
    data: Optional[pd.DataFrame] = None
    status_code: Optional[int] = None
    execution_time: float = 0.0
    record_count: int = 0
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    content_type: str = ""


class WebScraper:
    """
    Robust, production-grade web scraping client.
    Handles requests, timeouts, retries, headers, and parsing pipelines.
    """

    SUPPORTED_TYPES = {
        "Page Title": scrape_title,
        "Headings": scrape_headings,
        "Links": scrape_links,
        "Paragraphs": scrape_paragraphs,
        "Tables": scrape_tables,
        "Images": scrape_images,
    }

    def __init__(self, timeout: int = 10, user_agent: str = DEFAULT_USER_AGENT):
        self.timeout = timeout
        self.user_agent = user_agent
        self.session = requests.Session()

    def _get_headers(self, custom_ua: Optional[str] = None) -> dict:
        return {
            "User-Agent": custom_ua or self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "DNT": "1",  # Do Not Track request header
        }

    def scrape(
        self,
        url: str,
        scrape_type: str = "Links",
        max_records: Optional[int] = 100,
        check_robots: bool = False,
        custom_user_agent: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Execute full scraping workflow:
        1. Validate URL.
        2. Optionally check robots.txt.
        3. Send HTTP GET request with realistic headers.
        4. Validate status code and content-type.
        5. Parse HTML with BeautifulSoup.
        6. Extract and clean target data into a Pandas DataFrame.
        """
        run_logs: List[str] = []

        def log_msg(level: str, text: str):
            formatted = f"[{level}] {text}"
            run_logs.append(formatted)
            if level == "INFO":
                logger.info(text)
            elif level == "WARNING":
                logger.warning(text)
            elif level == "ERROR":
                logger.error(text)

        start_time = time.perf_counter()
        log_msg("INFO", "Scraping process initiated.")

        # Step 1: Validate URL
        is_valid, validation_err = validate_url(url)
        if not is_valid:
            log_msg("ERROR", f"URL validation failed: {validation_err}")
            return ScrapeResult(
                success=False,
                url=url,
                scrape_type=scrape_type,
                error_message=f"❌ Invalid URL: {validation_err}",
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )

        clean_url = sanitize_url(url)
        log_msg("INFO", f"URL validated: {clean_url}")

        # Step 2: Robots.txt check (if enabled)
        if check_robots:
            log_msg("INFO", "Checking robots.txt permission...")
            ua_for_robots = custom_user_agent or self.user_agent
            is_allowed, reason = check_robots_permission(clean_url, user_agent=ua_for_robots)
            if not is_allowed:
                log_msg("WARNING", f"Robots.txt check: {reason}")
                return ScrapeResult(
                    success=False,
                    url=clean_url,
                    scrape_type=scrape_type,
                    error_message=f"🚫 Scraping disallowed by target website's robots.txt policy ({reason}).",
                    logs=run_logs,
                    execution_time=round(time.perf_counter() - start_time, 2),
                )
            log_msg("INFO", f"Robots.txt check passed: {reason}")

        # Step 3: Fetch HTML via HTTP GET
        log_msg("INFO", f"Sending HTTP request to server (Timeout={self.timeout}s)...")
        headers = self._get_headers(custom_user_agent)

        try:
            response = self.session.get(
                clean_url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            status_code = response.status_code
            content_type = response.headers.get("Content-Type", "")
            log_msg("INFO", f"HTTP Response received. Status Code: {status_code}, Content-Type: {content_type}")

        except requests.exceptions.Timeout:
            err_msg = f"⏱️ Connection timeout: The target server at '{clean_url}' did not respond within {self.timeout} seconds."
            log_msg("ERROR", err_msg)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                error_message=err_msg,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )
        except requests.exceptions.SSLError as ssl_err:
            err_msg = f"🔒 SSL Certificate Verification Failed: {str(ssl_err)}"
            log_msg("ERROR", err_msg)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                error_message=f"❌ Unable to establish secure HTTPS connection. The website's SSL certificate may be invalid.",
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )
        except requests.exceptions.ConnectionError:
            err_msg = f"❌ Connection Error: Unable to reach '{clean_url}'. The domain might be down, invalid, or blocking connections."
            log_msg("ERROR", err_msg)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                error_message=err_msg,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )
        except requests.exceptions.RequestException as req_err:
            err_msg = f"❌ HTTP Request Exception: {str(req_err)}"
            log_msg("ERROR", err_msg)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                error_message=err_msg,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )

        # Step 4: Handle HTTP Status Codes
        if status_code == 403:
            err = "🚫 HTTP 403 Forbidden: Access denied by target server. The website may require authentication or block automated requests."
            log_msg("ERROR", err)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                status_code=403,
                error_message=err,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )
        elif status_code == 404:
            err = f"🔍 HTTP 404 Not Found: The requested URL '{clean_url}' does not exist on the server."
            log_msg("ERROR", err)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                status_code=404,
                error_message=err,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )
        elif status_code >= 500:
            err = f"⚠️ Server Error (HTTP {status_code}): The remote server encountered an error while processing the request."
            log_msg("ERROR", err)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                status_code=status_code,
                error_message=err,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )
        elif status_code != 200:
            err = f"⚠️ Unexpected HTTP Status Code: {status_code}."
            log_msg("WARNING", err)

        # Step 5: Check Content-Type & Empty Body
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            log_msg("WARNING", f"Content-Type '{content_type}' might not be an HTML document.")

        html_text = response.text
        if not html_text or not html_text.strip():
            err = "📄 Empty Webpage: The server responded with an empty content body."
            log_msg("ERROR", err)
            return ScrapeResult(
                success=False,
                url=clean_url,
                scrape_type=scrape_type,
                status_code=status_code,
                error_message=err,
                logs=run_logs,
                execution_time=round(time.perf_counter() - start_time, 2),
            )

        log_msg("INFO", f"HTML fetched successfully ({len(html_text):,} bytes). Parsing document...")

        # Step 6: Parse HTML with BeautifulSoup & Extract Data
        return self._parse_and_extract(
            html_content=html_text,
            url=clean_url,
            scrape_type=scrape_type,
            max_records=max_records,
            status_code=status_code,
            content_type=content_type,
            start_time=start_time,
            run_logs=run_logs,
        )

    def scrape_html(
        self,
        html_content: str,
        scrape_type: str = "Links",
        base_url: str = "http://demo.local",
        max_records: Optional[int] = 100,
    ) -> ScrapeResult:
        """
        Scrape directly from an in-memory HTML string.
        Used for local offline testing or the built-in test bench.
        """
        run_logs: List[str] = [
            "[INFO] Scraping from local HTML test bench.",
            f"[INFO] Content length: {len(html_content):,} characters.",
        ]
        start_time = time.perf_counter()
        return self._parse_and_extract(
            html_content=html_content,
            url=base_url,
            scrape_type=scrape_type,
            max_records=max_records,
            status_code=200,
            content_type="text/html; charset=utf-8",
            start_time=start_time,
            run_logs=run_logs,
        )

    def _parse_and_extract(
        self,
        html_content: str,
        url: str,
        scrape_type: str,
        max_records: Optional[int],
        status_code: int,
        content_type: str,
        start_time: float,
        run_logs: List[str],
    ) -> ScrapeResult:
        """Helper to invoke the selected parser and build the ScrapeResult."""
        try:
            # Prefer lxml for high performance, fallback to html.parser
            try:
                soup = BeautifulSoup(html_content, "lxml")
            except Exception:
                soup = BeautifulSoup(html_content, "html.parser")

            parser_func = self.SUPPORTED_TYPES.get(scrape_type)
            if not parser_func:
                err = f"Unknown scraping type '{scrape_type}'. Supported: {list(self.SUPPORTED_TYPES.keys())}"
                run_logs.append(f"[ERROR] {err}")
                return ScrapeResult(
                    success=False,
                    url=url,
                    scrape_type=scrape_type,
                    error_message=err,
                    logs=run_logs,
                    execution_time=round(time.perf_counter() - start_time, 2),
                )

            run_logs.append(f"[INFO] Running parser for '{scrape_type}'...")
            
            if scrape_type == "Page Title":
                df = parser_func(soup, base_url=url)
            else:
                df = parser_func(soup, base_url=url, max_records=max_records)

            record_count = len(df)
            elapsed = round(time.perf_counter() - start_time, 2)

            if record_count == 0:
                msg = f"ℹ️ Notice: No '{scrape_type}' elements were found on this webpage."
                run_logs.append(f"[WARNING] 0 records extracted.")
                return ScrapeResult(
                    success=True,
                    url=url,
                    scrape_type=scrape_type,
                    data=df,
                    status_code=status_code,
                    record_count=0,
                    execution_time=elapsed,
                    error_message=msg,
                    logs=run_logs,
                    content_type=content_type,
                )

            run_logs.append(f"[SUCCESS] Successfully extracted {record_count} records in {elapsed}s.")
            return ScrapeResult(
                success=True,
                url=url,
                scrape_type=scrape_type,
                data=df,
                status_code=status_code,
                record_count=record_count,
                execution_time=elapsed,
                logs=run_logs,
                content_type=content_type,
            )

        except Exception as exc:
            elapsed = round(time.perf_counter() - start_time, 2)
            err = f"❌ Parsing Error: An unexpected error occurred while parsing HTML: {str(exc)}"
            run_logs.append(f"[ERROR] {err}")
            return ScrapeResult(
                success=False,
                url=url,
                scrape_type=scrape_type,
                error_message=err,
                logs=run_logs,
                execution_time=elapsed,
            )
