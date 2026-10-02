"""
Web Scraping Automation Dashboard
A state-of-the-art web data extraction platform built with Streamlit & Python.
Theme: Cyber Emerald & Obsidian Gold.
Features multi-format export, SQLite audit logging, robots.txt compliance, and offline testing.
"""

from datetime import datetime
import json
import os
import time
from urllib.parse import urlparse
import pandas as pd
import streamlit as st

# Application Module Imports
from database.db import (
    clear_history,
    delete_history_item,
    get_history,
    get_history_by_id,
    get_stats,
    init_db,
    save_history,
)
from scraper.scraper import DEFAULT_USER_AGENT, ScrapeResult, WebScraper
from scraper.validators import check_robots_permission, sanitize_url, validate_url
from utils.export import export_to_csv, export_to_excel, export_to_json
from utils.logger import clear_ui_logs, get_logs_for_ui, setup_logger

# ---------------------------------------------------------
# Page Configuration & Global Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Web Scraping Automation",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize application logger and database
app_logger = setup_logger()
init_db()

# Path to local demo HTML file
DEMO_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "demo_page.html")

# ---------------------------------------------------------
# Advanced Custom Styling (Cyber Emerald & Obsidian Theme)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* Import Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Hero Header & Gradient Titles */
        .hero-title {
            font-size: 2.3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #10B981 0%, #34D399 35%, #6366F1 75%, #A855F7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-size: 0.95rem;
            color: #94A3B8;
            margin-bottom: 20px;
            font-weight: 400;
        }

        /* Feature Cards Grid */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 24px;
        }
        .feature-card {
            background: linear-gradient(145deg, rgba(22, 31, 48, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 12px;
            padding: 16px 18px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #10B981, #6366F1);
            opacity: 0.7;
        }
        .feature-card:hover {
            transform: translateY(-2px);
            border-color: rgba(16, 185, 129, 0.5);
            box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.15);
        }
        .feature-icon {
            font-size: 1.5rem;
            margin-bottom: 8px;
        }
        .feature-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #F1F5F9;
            margin-bottom: 4px;
        }
        .feature-desc {
            font-size: 0.78rem;
            color: #94A3B8;
            line-height: 1.4;
        }

        /* Executive KPI Metrics */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: linear-gradient(145deg, #161F30 0%, #0E1626 100%);
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 18px 20px;
            position: relative;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }
        .kpi-title {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94A3B8;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .kpi-value-emerald {
            font-size: 2.1rem;
            font-weight: 800;
            color: #10B981;
            line-height: 1.1;
        }
        .kpi-value-violet {
            font-size: 2.1rem;
            font-weight: 800;
            color: #A855F7;
            line-height: 1.1;
        }
        .kpi-value-cyan {
            font-size: 1.3rem;
            font-weight: 700;
            color: #38BDF8;
            line-height: 1.3;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .kpi-value-gold {
            font-size: 1.25rem;
            font-weight: 700;
            color: #F59E0B;
            line-height: 1.3;
        }

        /* Status Badges */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 14px;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .status-ready {
            background: rgba(148, 163, 184, 0.15);
            color: #CBD5E1;
            border: 1px solid rgba(148, 163, 184, 0.3);
        }
        .status-scraping {
            background: rgba(245, 158, 11, 0.15);
            color: #FCD34D;
            border: 1px solid rgba(245, 158, 11, 0.4);
            animation: pulse 1.5s infinite;
        }
        .status-completed {
            background: rgba(16, 185, 129, 0.15);
            color: #6EE7B7;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .status-failed {
            background: rgba(239, 68, 68, 0.15);
            color: #FCA5A5;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }

        /* Cyber Terminal Console */
        .terminal-box {
            background-color: #060911;
            color: #10B981;
            font-family: 'JetBrains Mono', Courier, monospace;
            padding: 16px 20px;
            border-radius: 10px;
            border: 1px solid rgba(16, 185, 129, 0.25);
            height: 330px;
            overflow-y: auto;
            font-size: 0.85rem;
            line-height: 1.6;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.6);
        }
        .log-info { color: #38BDF8; }
        .log-success { color: #34D399; font-weight: 600; }
        .log-warning { color: #FBBF24; }
        .log-error { color: #F87171; font-weight: 600; }

        /* Sidebar Styling */
        .sidebar-brand-box {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(99, 102, 241, 0.12) 100%);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 18px;
        }
        .sidebar-brand {
            font-size: 1.15rem;
            font-weight: 800;
            color: #10B981;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .sidebar-sub {
            font-size: 0.75rem;
            color: #94A3B8;
            margin-top: 4px;
        }

        @keyframes pulse {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = None
if "scrape_status" not in st.session_state:
    st.session_state.scrape_status = "Ready"
if "scrape_stats" not in st.session_state:
    st.session_state.scrape_stats = {
        "records": 0,
        "time": 0.0,
        "url": "None",
        "timestamp": "Never",
        "type": "None",
    }
if "current_logs" not in st.session_state:
    st.session_state.current_logs = [
        "[INFO] Web Scraping Engine initialized in standby mode.",
        "[INFO] Select a public target or choose an instant preset to begin.",
    ]
if "url_input" not in st.session_state:
    st.session_state.url_input = "https://quotes.toscrape.com/"
if "error_message" not in st.session_state:
    st.session_state.error_message = None


# ---------------------------------------------------------
# Sidebar Configuration Deck
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-box">
            <div class="sidebar-brand">🕸️ Scraping Engine</div>
            <div class="sidebar-sub">Automated Extraction & Compliance Hub</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Preset Demo Websites
    st.markdown("##### ⚡ Quick Target Presets")
    demo_choice = st.selectbox(
        "Choose Verified Demo Target:",
        [
            "Select preset...",
            "💬 Quotes to Scrape (Quotes & Authors)",
            "📚 Books to Scrape (Titles & Pricing)",
            "🧪 Local Test Bench (Zero Internet)",
            "🌐 Wikipedia Sample (Structured Tables)",
        ],
        index=0,
    )

    if demo_choice == "💬 Quotes to Scrape (Quotes & Authors)":
        st.session_state.url_input = "https://quotes.toscrape.com/"
    elif demo_choice == "📚 Books to Scrape (Titles & Pricing)":
        st.session_state.url_input = "https://books.toscrape.com/"
    elif demo_choice == "🧪 Local Test Bench (Zero Internet)":
        st.session_state.url_input = "http://demo.local/test-bench"
    elif demo_choice == "🌐 Wikipedia Sample (Structured Tables)":
        st.session_state.url_input = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"

    st.markdown("---")

    # URL Input Field
    target_url = st.text_input(
        "🌐 Target Website URL",
        value=st.session_state.url_input,
        placeholder="https://example.com",
        help="Input any public, unauthenticated HTTP or HTTPS webpage URL.",
    )
    st.session_state.url_input = target_url

    # Scraping Type
    scrape_type = st.selectbox(
        "🎯 Extraction Target Mode",
        [
            "Headings",
            "Links",
            "Tables",
            "Paragraphs",
            "Page Title",
            "Images",
        ],
        index=0,
        help="Choose the HTML entity type to extract into structured rows.",
    )

    # Maximum Records
    max_records = st.slider(
        "🔢 Record Limit Cap",
        min_value=5,
        max_value=300,
        value=50,
        step=5,
        help="Controls the maximum number of extracted records returned.",
    )

    # Advanced Settings
    with st.expander("⚙️ Advanced Parameters"):
        timeout_seconds = st.slider("HTTP Timeout (seconds)", min_value=3, max_value=30, value=10)
        check_robots = st.checkbox("Audit robots.txt Before Crawl", value=False, help="Verifies crawling permissions against target site's robots.txt.")
        custom_ua = st.text_input(
            "Custom User-Agent Header",
            value="",
            placeholder="Default Chrome agent",
            help="Custom user-agent string override.",
        )

    st.markdown("---")

    # Action Buttons
    col_btn1, col_btn2 = st.columns(2)
    start_clicked = col_btn1.button("🚀 Launch Scrape", type="primary", use_container_width=True)
    clear_clicked = col_btn2.button("🔄 Reset Canvas", use_container_width=True)

    if clear_clicked:
        st.session_state.scraped_data = None
        st.session_state.scrape_status = "Ready"
        st.session_state.error_message = None
        st.session_state.scrape_stats = {
            "records": 0,
            "time": 0.0,
            "url": "None",
            "timestamp": "Never",
            "type": "None",
        }
        st.session_state.current_logs = [
            "[INFO] Workspace reset.",
            "[INFO] Ready for new extraction task.",
        ]
        st.rerun()


# ---------------------------------------------------------
# Execution Handler
# ---------------------------------------------------------
if start_clicked:
    st.session_state.error_message = None
    st.session_state.scrape_status = "Scraping..."
    st.session_state.current_logs = []

    # Check if user picked the local test bench
    if target_url.strip() in ("http://demo.local/test-bench", "demo.local"):
        st.session_state.current_logs.append("[INFO] Loading offline local HTML test bench...")
        try:
            if os.path.exists(DEMO_HTML_PATH):
                with open(DEMO_HTML_PATH, "r", encoding="utf-8") as f:
                    local_html = f.read()
                scraper = WebScraper()
                result = scraper.scrape_html(
                    html_content=local_html,
                    scrape_type=scrape_type,
                    base_url="https://technova.local",
                    max_records=max_records,
                )
            else:
                result = ScrapeResult(
                    success=False,
                    url=target_url,
                    scrape_type=scrape_type,
                    error_message=f"Local demo file not found at {DEMO_HTML_PATH}",
                    logs=["[ERROR] Local demo file missing."],
                )
        except Exception as exc:
            result = ScrapeResult(
                success=False,
                url=target_url,
                scrape_type=scrape_type,
                error_message=f"Local parse error: {str(exc)}",
                logs=[f"[ERROR] {str(exc)}"],
            )
    else:
        # Standard live HTTP scrape
        scraper = WebScraper(
            timeout=timeout_seconds,
            user_agent=custom_ua.strip() if custom_ua.strip() else DEFAULT_USER_AGENT,
        )
        result = scraper.scrape(
            url=target_url,
            scrape_type=scrape_type,
            max_records=max_records,
            check_robots=check_robots,
            custom_user_agent=custom_ua.strip() if custom_ua.strip() else None,
        )

    # Process and record results
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.current_logs = result.logs

    if result.success and result.data is not None and not result.data.empty:
        st.session_state.scrape_status = "Completed"
        st.session_state.scraped_data = result.data
        st.session_state.scrape_stats = {
            "records": result.record_count,
            "time": result.execution_time,
            "url": result.url,
            "timestamp": now_str,
            "type": result.scrape_type,
        }

        # Save to SQLite History
        save_history(
            url=result.url,
            scrape_type=result.scrape_type,
            record_count=result.record_count,
            status="Success",
            execution_time=result.execution_time,
            preview_df=result.data,
        )
    elif result.success and (result.data is None or result.data.empty):
        # 0 records found but request was technically 200 OK
        st.session_state.scrape_status = "Completed"
        st.session_state.scraped_data = pd.DataFrame()
        st.session_state.error_message = result.error_message or f"ℹ️ 0 {scrape_type} records found on this page."
        st.session_state.scrape_stats = {
            "records": 0,
            "time": result.execution_time,
            "url": result.url,
            "timestamp": now_str,
            "type": result.scrape_type,
        }
        save_history(
            url=result.url,
            scrape_type=result.scrape_type,
            record_count=0,
            status="Success",
            execution_time=result.execution_time,
            error_message="0 records found",
        )
    else:
        st.session_state.scrape_status = "Failed"
        st.session_state.scraped_data = None
        st.session_state.error_message = result.error_message or "An unexpected failure occurred during scraping."
        st.session_state.scrape_stats = {
            "records": 0,
            "time": result.execution_time,
            "url": result.url,
            "timestamp": now_str,
            "type": result.scrape_type,
        }

        # Save failure to SQLite
        save_history(
            url=result.url,
            scrape_type=result.scrape_type,
            record_count=0,
            status="Failed",
            execution_time=result.execution_time,
            error_message=result.error_message,
        )


# ---------------------------------------------------------
# Top Header & Status Section
# ---------------------------------------------------------
col_head_left, col_head_right = st.columns([3, 1])
with col_head_left:
    st.markdown('<div class="hero-title">🕸️ Web Scraping Automation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">'
        'Automated Web Data Extraction, Ethical Auditing & Analytical Export Platform • Built with Python & Streamlit'
        '</div>',
        unsafe_allow_html=True,
    )

with col_head_right:
    status_label = st.session_state.scrape_status
    if status_label == "Ready":
        badge_cls = "status-ready"
        icon = "⚪"
    elif status_label == "Scraping...":
        badge_cls = "status-scraping"
        icon = "⏳"
    elif status_label == "Completed":
        badge_cls = "status-completed"
        icon = "✅"
    else:
        badge_cls = "status-failed"
        icon = "❌"

    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 10px;">
            <span style="color: #94A3B8; font-size: 0.8rem; margin-right: 8px;">ENGINE STATUS:</span>
            <span class="status-badge {badge_cls}">{icon} {status_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Section 1: Redesigned Feature Highlights Grid
# ---------------------------------------------------------
st.markdown(
    """
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🏷️</div>
            <div class="feature-title">Headings Hierarchy</div>
            <div class="feature-desc">Extracts H1–H6 elements in visual order for document structure & SEO auditing.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔗</div>
            <div class="feature-title">Hyperlink Harvester</div>
            <div class="feature-desc">Resolves relative paths to absolute URLs and classifies internal vs external links.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Table Structuring</div>
            <div class="feature-desc">Auto-detects thead/tbody headers, pads irregular rows, and converts tables to DataFrames.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <div class="feature-title">Robots & SSRF Guard</div>
            <div class="feature-desc">Audits robots.txt directives and blocks private IP ranges to ensure ethical compliance.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Section 2: Executive KPI Ribbon (Metric Cards)
# ---------------------------------------------------------
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">📊 Records Extracted</div>
            <div class="kpi-value-emerald">{st.session_state.scrape_stats['records']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">⚡ Execution Latency</div>
            <div class="kpi-value-violet">{st.session_state.scrape_stats['time']:.2f}s</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m3:
    domain_display = "Standby"
    if st.session_state.scrape_stats["url"] != "None":
        parsed = urlparse(st.session_state.scrape_stats["url"])
        domain_display = parsed.netloc or parsed.path[:22]

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">🌐 Target Host</div>
            <div class="kpi-value-cyan" title="{domain_display}">{domain_display}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m4:
    last_time = st.session_state.scrape_stats['timestamp']
    display_time = last_time.split(' ')[-1] if last_time != "Never" else "Never"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">🕒 Timestamp</div>
            <div class="kpi-value-gold">{display_time}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Error Banner
if st.session_state.error_message:
    if "ℹ️" in st.session_state.error_message:
        st.info(st.session_state.error_message)
    else:
        st.error(st.session_state.error_message)


# ---------------------------------------------------------
# Section 3: Interactive Workspace Tabs
# ---------------------------------------------------------
tab_data, tab_logs, tab_history, tab_robots, tab_demo, tab_guide = st.tabs([
    "📊 Scraped Data Hub",
    "⚡ Live Telemetry Logs",
    "🗄️ SQLite Audit History",
    "🛡️ robots.txt Auditor",
    "🧪 Offline Test Bench",
    "💡 Technical Architecture & Pitch",
])

# ---------------------------------------------------------
# Tab 1: Scraped Data Hub
# ---------------------------------------------------------
with tab_data:
    df_current = st.session_state.scraped_data

    if df_current is not None and not df_current.empty:
        col_down1, col_down2, col_down3, col_info = st.columns([1.2, 1.2, 1.2, 2.5])

        csv_bytes = export_to_csv(df_current)
        excel_bytes = export_to_excel(df_current)
        json_bytes = export_to_json(df_current)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scrape_slug = st.session_state.scrape_stats["type"].lower().replace(" ", "_")

        with col_down1:
            st.download_button(
                label="📥 Download CSV (BOM)",
                data=csv_bytes,
                file_name=f"scraped_{scrape_slug}_{stamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_down2:
            st.download_button(
                label="📊 Download Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"scraped_{scrape_slug}_{stamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_down3:
            st.download_button(
                label="📋 Download JSON",
                data=json_bytes,
                file_name=f"scraped_{scrape_slug}_{stamp}.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_info:
            st.markdown(
                f"<div style='text-align: right; padding-top: 8px; color: #10B981; font-weight: 600; font-size: 0.9rem;'>"
                f"✅ Extracted {len(df_current)} Rows × {len(df_current.columns)} Columns"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Interactive Table
        st.dataframe(
            df_current,
            use_container_width=True,
            hide_index=True,
        )

    elif df_current is not None and df_current.empty:
        st.warning("⚠️ Request returned HTTP 200 OK, but 0 matching elements were found on the page.")
    else:
        st.info("👋 Ready to scrape. Enter a target URL in the sidebar or pick a preset, then click **'🚀 Launch Scrape'**.")


# ---------------------------------------------------------
# Tab 2: Live Telemetry Logs
# ---------------------------------------------------------
with tab_logs:
    col_log_head, col_log_clear = st.columns([5, 1])
    col_log_head.markdown("#### ⚡ Realtime Network & Parsing Telemetry")
    if col_log_clear.button("Clear Log View", use_container_width=True):
        st.session_state.current_logs = ["[INFO] Telemetry buffer cleared."]
        st.rerun()

    log_html_lines = []
    for line in st.session_state.current_logs:
        if "[ERROR]" in line:
            cls = "log-error"
        elif "[WARNING]" in line:
            cls = "log-warning"
        elif "[SUCCESS]" in line:
            cls = "log-success"
        else:
            cls = "log-info"
        log_html_lines.append(f"<div class='{cls}'>{line}</div>")

    st.markdown(
        f"""
        <div class="terminal-box">
            {''.join(log_html_lines)}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Telemetry traces network DNS handshake, HTTP status validation, DOM parsing, and deduplication passes.")


# ---------------------------------------------------------
# Tab 3: SQLite Audit History
# ---------------------------------------------------------
with tab_history:
    st.markdown("#### 🗄️ Relational Audit Trail (SQLite)")

    # Aggregate Statistics
    db_stats = get_stats()
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    col_h1.metric("Cumulative Jobs", db_stats["total_scrapes"])
    col_h2.metric("Successful Jobs", db_stats["successful"])
    col_h3.metric("Success Rate", f"{db_stats['success_rate']}%")
    col_h4.metric("Total Records Saved", f"{db_stats['total_records']:,}")

    st.markdown("---")

    # Filters
    col_f1, col_f2, col_f3 = st.columns([3, 2, 1])
    search_term = col_f1.text_input("🔍 Search History by Domain or Mode", placeholder="e.g. quotes, books, headings...")
    status_sel = col_f2.selectbox("Filter Status", ["All", "Success", "Failed"])

    if col_f3.button("🗑️ Clear History", use_container_width=True, help="Wipes all historical entries from SQLite"):
        clear_history()
        st.success("Scraping history cleared successfully.")
        st.rerun()

    # Load History Table
    df_history = get_history(search_query=search_term, status_filter=status_sel, limit=50)

    if not df_history.empty:
        st.dataframe(
            df_history,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Target URL": st.column_config.LinkColumn("Target URL"),
            },
        )

        # Inspect Record Detail
        st.markdown("##### 🔎 Stored Data Preview Inspector")
        job_ids = df_history["Job ID"].tolist()
        selected_job_id = st.selectbox("Select Job ID to view stored preview:", job_ids)

        if selected_job_id:
            job_details = get_history_by_id(selected_job_id)
            if job_details and job_details.get("preview_json"):
                try:
                    preview_data = json.loads(job_details["preview_json"])
                    preview_df = pd.DataFrame(preview_data)
                    st.write(f"Snapshot preview of top records captured on {job_details['timestamp']}:")
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)
                except Exception:
                    st.write(job_details["preview_json"])
            elif job_details:
                st.info(f"No tabular snapshot was saved for this job (Status: {job_details.get('status')}). Notes: {job_details.get('error_message') or 'N/A'}")
    else:
        st.info("No audit history found matching current filters.")


# ---------------------------------------------------------
# Tab 4: robots.txt Auditor & Ethical Scraping
# ---------------------------------------------------------
with tab_robots:
    st.markdown("#### 🛡️ Compliance & robots.txt Protocol Auditor")
    st.write(
        "Ethical web data extraction requires compliance with the target site's Robots Exclusion Standard (`/robots.txt`). "
        "Test any target URL to verify whether automated crawling is permitted."
    )

    col_r1, col_r2 = st.columns([3, 1])
    test_url = col_r1.text_input("Enter URL to audit:", value=st.session_state.url_input)
    audit_clicked = col_r2.button("🔍 Run Policy Audit", use_container_width=True)

    if audit_clicked and test_url:
        with st.spinner("Analyzing target robots.txt policy..."):
            allowed, explanation = check_robots_permission(test_url)
            if allowed:
                st.success(f"✅ **Crawling Permitted:** {explanation}")
            else:
                st.error(f"🚫 **Crawling Disallowed:** {explanation}")

    st.markdown("---")
    st.markdown(
        """
        ##### ⚖️ Core Ethical Principles Implemented in This System
        1. **Robots Protocol Adherence**: Respects `User-agent` and `Disallow` rules.
        2. **Rate Limiting & Low Concurrency**: Prevents Denial-of-Service (DoS) and reduces server load.
        3. **Transparent User-Agent**: Declares client software version rather than masking identity.
        4. **Public Data Exclusivity**: Bypassing logins, paywalls, or CAPTCHAs is strictly avoided.
        5. **SSRF Guard**: Resolves DNS and blocks internal private IP subnets (`127.0.0.1`, `10.x`, `192.168.x`).
        """
    )


# ---------------------------------------------------------
# Tab 5: Built-in Offline Test Bench
# ---------------------------------------------------------
with tab_demo:
    st.markdown("#### 🧪 Zero-Dependency Offline Test Bench")
    st.write(
        "Need to demonstrate the scraper in an environment with unstable Wi-Fi or firewall restrictions? "
        "This runs the extraction pipeline against an internal mock HTML document with complete data fidelity."
    )

    if st.button("🚀 Run Extraction on Built-in Test Bench", type="primary"):
        st.session_state.url_input = "http://demo.local/test-bench"
        if os.path.exists(DEMO_HTML_PATH):
            with open(DEMO_HTML_PATH, "r", encoding="utf-8") as f:
                local_html = f.read()
            scraper = WebScraper()
            result = scraper.scrape_html(
                html_content=local_html,
                scrape_type=scrape_type,
                base_url="https://technova.local",
                max_records=max_records,
            )
            st.session_state.scrape_status = "Completed"
            st.session_state.scraped_data = result.data
            st.session_state.scrape_stats = {
                "records": result.record_count,
                "time": result.execution_time,
                "url": "http://demo.local/test-bench",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": result.scrape_type,
            }
            st.session_state.current_logs = result.logs
            save_history(
                url="http://demo.local/test-bench",
                scrape_type=result.scrape_type,
                record_count=result.record_count,
                status="Success",
                execution_time=result.execution_time,
                preview_df=result.data,
            )
            st.success(f"Successfully extracted {result.record_count} records from the offline test bench! Check the '📊 Scraped Data Hub' tab.")
        else:
            st.error("Demo HTML file not found.")

    with st.expander("📄 View Offline Test Bench HTML Source"):
        if os.path.exists(DEMO_HTML_PATH):
            with open(DEMO_HTML_PATH, "r", encoding="utf-8") as f:
                st.code(f.read(), language="html")


# ---------------------------------------------------------
# Tab 6: Technical Architecture & Interview Pitch
# ---------------------------------------------------------
with tab_guide:
    st.markdown("#### 💡 Technical Architecture & Interview Talking Points")
    st.markdown(
        """
        ##### 🏗️ System Workflow
        `User Input (Streamlit)` ➔ `SSRF & Schema Validation` ➔ `robots.txt Check` ➔ `Requests Session (User-Agent)` ➔ `BeautifulSoup4 + lxml Parsing` ➔ `Pandas Cleaning & Deduplication` ➔ `SQLite Audit Log` ➔ `CSV (UTF-8 BOM) & Styled Excel Export`

        ##### 🎯 Why this stack was selected:
        - **Requests vs. Selenium**: For static pages, Selenium incurs 10x overhead by booting Chromium. Requests executes in milliseconds with minimal RAM.
        - **BeautifulSoup4 vs. Regex**: Regex on nested HTML is brittle. BeautifulSoup constructs a fault-tolerant DOM tree that parses malformed tags gracefully.
        - **Pandas**: Delivers instant normalization, column alignment, whitespace cleaning, and export serialization.
        - **SQLite**: Zero-configuration embedded ACID storage with no database server maintenance required.
        - **UTF-8 BOM (`utf-8-sig`)**: Prevents character corruption (mojibake) when CSV files are opened in Microsoft Excel on Windows.
        """
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748B; font-size: 0.85rem; padding: 15px 0;">
        <span style="color: #10B981; font-weight: 700;">Web Scraping Automation Platform</span> • Production & Interview Ready<br>
        Crafted with Python 3.12, Streamlit, Requests, BeautifulSoup4, Pandas, OpenPyXL & SQLite • Hosted on Render
    </div>
    """,
    unsafe_allow_html=True,
)
