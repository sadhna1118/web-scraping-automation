"""
URL and Compliance Validators
Validates web URLs and checks ethical scraping compliance (e.g., robots.txt).
"""

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse
import urllib.robotparser


def sanitize_url(url: str) -> str:
    """
    Sanitize and normalize a raw URL input.
    - Trims leading/trailing whitespace.
    - Adds https:// scheme if no scheme is specified.
    """
    if not url:
        return ""
    
    clean_url = url.strip()
    parsed = urlparse(clean_url)
    
    # If scheme is missing (e.g. "quotes.toscrape.com"), default to https://
    if not parsed.scheme:
        clean_url = "https://" + clean_url
        
    return clean_url


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate that the given URL has a proper HTTP/HTTPS scheme and valid domain.
    Returns (is_valid, error_message).
    """
    if not url or not url.strip():
        return False, "URL cannot be empty. Please enter a valid website address."

    clean_url = sanitize_url(url)
    try:
        parsed = urlparse(clean_url)
    except Exception as exc:
        return False, f"Malformed URL: {str(exc)}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Invalid protocol '{parsed.scheme}'. Only 'http://' and 'https://' are supported."

    if not parsed.netloc:
        return False, "Invalid URL structure. Missing host or domain name (e.g., https://example.com)."

    # Domain syntax check
    domain = parsed.netloc.split(":")[0]  # strip port if present
    if "." not in domain and domain != "localhost":
        return False, f"Invalid domain name '{domain}'. Expected format like 'example.com'."

    return True, ""


def is_private_ip(hostname: str) -> bool:
    """
    Check if a hostname resolves to a private or loopback IP address (SSRF mitigation).
    """
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local
    except Exception:
        # If DNS resolution fails, allow downstream handler to catch connection error
        return False


def check_robots_permission(url: str, user_agent: str = "*", timeout: int = 5) -> tuple[bool, str]:
    """
    Check whether scraping the target URL path is permitted under the site's robots.txt.
    Returns (is_allowed, explanation).
    """
    clean_url = sanitize_url(url)
    parsed = urlparse(clean_url)
    if not parsed.netloc:
        return False, "Cannot verify robots.txt: invalid domain."

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()

    try:
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(user_agent, clean_url)
        if allowed:
            return True, f"Allowed by {robots_url} for user-agent '{user_agent}'."
        else:
            return False, f"Disallowed by {robots_url} for user-agent '{user_agent}'."
    except Exception as exc:
        # Many sites don't have robots.txt or return 404; standard practice is permissive crawling
        return True, f"robots.txt could not be fetched ({str(exc)}). Defaulting to permissible public access."
