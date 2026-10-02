"""
Web Scraping Automation Dashboard
A modern, production-grade web scraping interface built with Streamlit.
Features live data extraction, Pandas transformation, SQLite history tracking,
and multi-format export (CSV, Excel, JSON).
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
# Custom Styling (CSS Injection)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* Card & Metric Styling */
        .metric-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px 20px;
            color: #f8fafc;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            margin-bottom: 12px;
        }
        .metric-title {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #38bdf8;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-ready { background-color: #334155; color: #cbd5e1; }
        .status-scraping { background-color: #d97706; color: #fef3c7; }
        .status-completed { background-color: #166534; color: #bbf7d0; }
        .status-failed { background-color: #991b1b; color: #fecaca; }

        /* Terminal Console for Logs */
        .terminal-box {
            background-color: #0b0f19;
            color: #10b981;
            font-family: 'Courier New', Courier, monospace;
            padding: 14px 18px;
            border-radius: 8px;
            border: 1px solid #1e293b;
            height: 320px;
            overflow-y: auto;
            font-size: 0.85rem;
            line-height: 1.5;
        }
        .log-info { color: #38bdf8; }
        .log-success { color: #4ade80; }
        .log-warning { color: #facc15; }
        .log-error { color: #f87171; }

        /* Sidebar Header */
        .sidebar-brand {
            font-size: 1.3rem;
            font-weight: 800;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 2px;
        }
        .sidebar-sub {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-bottom: 20px;
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
        "[INFO] System initialized. Ready to scrape.",
        "[INFO] Select a preset or enter a public website URL.",
    ]
if "url_input" not in st.session_state:
    st.session_state.url_input = "https://quotes.toscrape.com/"
if "error_message" not in st.session_state:
    st.session_state.error_message = None


# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🕸️ Web Scraping Automation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Automated Web Data Extraction & Export Platform</div>', unsafe_allow_html=True)

    # Preset Demo Websites
    st.markdown("#### ⚡ Quick Demo Targets")
    demo_choice = st.selectbox(
        "Load Public Demo Preset:",
        [
            "Select preset...",
            "💬 Quotes to Scrape (Quotes, Authors, Tags)",
            "📚 Books to Scrape (Book Titles & Prices)",
            "🧪 Local Demo Page (Offline Test Bench)",
            "🌐 Wikipedia Countries (Sample Tables)",
        ],
        index=0,
    )

    if demo_choice == "💬 Quotes to Scrape (Quotes, Authors, Tags)":
        st.session_state.url_input = "https://quotes.toscrape.com/"
    elif demo_choice == "📚 Books to Scrape (Book Titles & Prices)":
        st.session_state.url_input = "https://books.toscrape.com/"
    elif demo_choice == "🧪 Local Demo Page (Offline Test Bench)":
        st.session_state.url_input = "http://demo.local/test-bench"
    elif demo_choice == "🌐 Wikipedia Countries (Sample Tables)":
        st.session_state.url_input = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"

    st.markdown("---")

    # URL Input Field
    target_url = st.text_input(
        "🌐 Target Website URL",
        value=st.session_state.url_input,
        placeholder="https://example.com",
        help="Enter any public, unauthenticated website URL (HTTP or HTTPS).",
    )
    st.session_state.url_input = target_url

    # Scraping Type
    scrape_type = st.selectbox(
        "🎯 Data Extraction Type",
        [
            "Headings",
            "Links",
            "Tables",
            "Paragraphs",
            "Page Title",
            "Images",
        ],
        index=0,
        help="Select what HTML elements to parse and extract into tabular format.",
    )

    # Maximum Records
    max_records = st.slider(
        "🔢 Maximum Records to Extract",
        min_value=5,
        max_value=300,
        value=50,
        step=5,
        help="Caps the number of rows returned to prevent memory exhaustion.",
    )

    # Advanced Settings
    with st.expander("⚙️ Advanced Request Settings"):
        timeout_seconds = st.slider("Request Timeout (seconds)", min_value=3, max_value=30, value=10)
        check_robots = st.checkbox("Check robots.txt Compliance", value=False, help="Verifies if robots.txt permits crawling the given path.")
        custom_ua = st.text_input(
            "Custom User-Agent",
            value="",
            placeholder="Default realistic Chrome agent",
            help="Optionally override the client User-Agent string.",
        )

    st.markdown("---")

    # Action Buttons
    col_btn1, col_btn2 = st.columns(2)
    start_clicked = col_btn1.button("🚀 Start Scraping", type="primary", use_container_width=True)
    clear_clicked = col_btn2.button("🗑️ Clear Results", use_container_width=True)

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
            "[INFO] Results cleared.",
            "[INFO] Ready for new scraping task.",
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
# Main Dashboard UI Layout
# ---------------------------------------------------------
# Header Area
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("🕸️ Web Scraping Automation")
    st.caption("Automated Web Data Extraction & Export Platform • Built with Python & Streamlit")

with col_head2:
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
        <div style="text-align: right; padding-top: 15px;">
            <span style="color: #94a3b8; font-size: 0.85rem; margin-right: 8px;">System Status:</span>
            <span class="status-badge {badge_cls}">{icon} {status_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Metric Statistics Cards
# ---------------------------------------------------------
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">📊 Records Extracted</div>
            <div class="metric-value">{st.session_state.scrape_stats['records']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">⏱️ Scraping Time</div>
            <div class="metric-value">{st.session_state.scrape_stats['time']:.2f}s</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m3:
    domain_display = "None"
    if st.session_state.scrape_stats["url"] != "None":
        parsed = urlparse(st.session_state.scrape_stats["url"])
        domain_display = parsed.netloc or parsed.path[:20]

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">🌐 Target Domain</div>
            <div class="metric-value" style="font-size: 1.25rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {domain_display}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">🕒 Last Run</div>
            <div class="metric-value" style="font-size: 1.1rem; color: #cbd5e1;">
                {st.session_state.scrape_stats['timestamp'].split(' ')[-1]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Error / Notification Banner
if st.session_state.error_message:
    if "ℹ️" in st.session_state.error_message:
        st.info(st.session_state.error_message)
    else:
        st.error(st.session_state.error_message)

# ---------------------------------------------------------
# Interactive Tabbed View
# ---------------------------------------------------------
tab_data, tab_logs, tab_history, tab_robots, tab_demo = st.tabs([
    "📊 Scraped Data",
    "📜 Scraping Logs",
    "🕒 Scraping History",
    "🛡️ robots.txt Auditor",
    "🧪 Offline Test Bench",
])

# ---------------------------------------------------------
# Tab 1: Scraped Data
# ---------------------------------------------------------
with tab_data:
    df_current = st.session_state.scraped_data

    if df_current is not None and not df_current.empty:
        col_down1, col_down2, col_down3, col_info = st.columns([1, 1, 1, 3])

        # Generate download payloads
        csv_bytes = export_to_csv(df_current)
        excel_bytes = export_to_excel(df_current)
        json_bytes = export_to_json(df_current)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scrape_slug = st.session_state.scrape_stats["type"].lower().replace(" ", "_")

        with col_down1:
            st.download_button(
                label="📥 Download CSV",
                data=csv_bytes,
                file_name=f"scraped_{scrape_slug}_{stamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_down2:
            st.download_button(
                label="📊 Download Excel",
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
                f"<div style='text-align: right; padding-top: 8px; color: #94a3b8; font-size: 0.9rem;'>"
                f"Displaying <b>{len(df_current)}</b> rows × <b>{len(df_current.columns)}</b> columns"
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
        st.warning("⚠️ No records to display. The parser completed successfully but found 0 matching elements.")
    else:
        st.info("👋 No data scraped yet. Enter a website URL in the sidebar and click **'🚀 Start Scraping'**.")


# ---------------------------------------------------------
# Tab 2: Scraping Logs
# ---------------------------------------------------------
with tab_logs:
    col_log_head, col_log_clear = st.columns([5, 1])
    col_log_head.markdown("#### 📜 Execution & System Logs")
    if col_log_clear.button("Clear Log View", use_container_width=True):
        st.session_state.current_logs = ["[INFO] Log view cleared."]
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
    st.caption("Logs display realtime events: network connection, header negotiation, HTML parsing, and record filtering.")


# ---------------------------------------------------------
# Tab 3: Scraping History
# ---------------------------------------------------------
with tab_history:
    st.markdown("#### 🕒 Scraping History & Job Registry")

    # Aggregate Statistics
    db_stats = get_stats()
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    col_h1.metric("Total Jobs", db_stats["total_scrapes"])
    col_h2.metric("Successful Scrapes", db_stats["successful"])
    col_h3.metric("Success Rate", f"{db_stats['success_rate']}%")
    col_h4.metric("Total Records Saved", f"{db_stats['total_records']:,}")

    st.markdown("---")

    # Filters
    col_f1, col_f2, col_f3 = st.columns([3, 2, 1])
    search_term = col_f1.text_input("🔍 Search History (URL or Type)", placeholder="Filter by domain or keyword...")
    status_sel = col_f2.selectbox("Filter by Status", ["All", "Success", "Failed"])
    
    if col_f3.button("🗑️ Clear History", use_container_width=True, help="Permanently delete all history records"):
        clear_history()
        st.success("History database cleared.")
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
        st.markdown("##### 🔎 Inspect Job Preview")
        job_ids = df_history["Job ID"].tolist()
        selected_job_id = st.selectbox("Select Job ID to view stored preview:", job_ids)

        if selected_job_id:
            job_details = get_history_by_id(selected_job_id)
            if job_details and job_details.get("preview_json"):
                try:
                    preview_data = json.loads(job_details["preview_json"])
                    preview_df = pd.DataFrame(preview_data)
                    st.write(f"Preview of top {len(preview_df)} records captured on {job_details['timestamp']}:")
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)
                except Exception:
                    st.write(job_details["preview_json"])
            elif job_details:
                st.info(f"No tabular preview was saved for this job (Status: {job_details.get('status')}). Notes: {job_details.get('error_message') or 'N/A'}")
    else:
        st.info("No scraping history found matching current filters.")


# ---------------------------------------------------------
# Tab 4: robots.txt Auditor & Ethical Scraping
# ---------------------------------------------------------
with tab_robots:
    st.markdown("#### 🛡️ robots.txt Policy Auditor")
    st.write(
        "Ethical web scraping strictly respects the target site's `robots.txt` protocol. "
        "Use this built-in auditor to test whether scraping a specific path is permitted by the remote server."
    )

    col_r1, col_r2 = st.columns([3, 1])
    test_url = col_r1.text_input("Enter URL to audit robots.txt:", value=st.session_state.url_input)
    audit_clicked = col_r2.button("🔍 Check robots.txt", use_container_width=True)

    if audit_clicked and test_url:
        with st.spinner("Checking target robots.txt policy..."):
            allowed, explanation = check_robots_permission(test_url)
            if allowed:
                st.success(f"✅ **Crawling Allowed:** {explanation}")
            else:
                st.error(f"🚫 **Crawling Disallowed:** {explanation}")

    st.markdown("---")
    st.markdown(
        """
        ##### ⚖️ Ethical Web Scraping Best Practices for Developers
        1. **Check robots.txt**: Always inspect `/robots.txt` before automating requests.
        2. **Rate Limiting**: Introduce delays between requests to prevent server overload or Denial of Service (DoS).
        3. **Identifiable User-Agent**: Provide a contact or identifier in the User-Agent header.
        4. **Respect Copyright & Terms**: Do not extract copyrighted, proprietary, or personal identifiable information (PII).
        5. **No Anti-Bot Bypass**: Never bypass CAPTCHAs, authentication paywalls, or encryption mechanisms.
        """
    )


# ---------------------------------------------------------
# Tab 5: Built-in Offline Test Bench
# ---------------------------------------------------------
with tab_demo:
    st.markdown("#### 🧪 Built-in Test Bench (Zero Internet Required)")
    st.write(
        "Demonstrate the scraper 100% reliably even without an internet connection or if the venue Wi-Fi is restricted. "
        "This runs the extraction algorithms against an internal, structured HTML document."
    )

    if st.button("🚀 Run Scraper on Built-in Test Bench", type="primary"):
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
            st.success(f"Extracted {result.record_count} records from the local test bench! Check the '📊 Scraped Data' tab.")
        else:
            st.error("Demo HTML file not found.")

    with st.expander("📄 View Local Test Bench HTML Source"):
        if os.path.exists(DEMO_HTML_PATH):
            with open(DEMO_HTML_PATH, "r", encoding="utf-8") as f:
                st.code(f.read(), language="html")


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 20px 0;">
        <b>Web Scraping Automation Platform</b> • Designed for Production & Live Technical Interviews<br>
        Built with Python 3.12, Streamlit, Requests, BeautifulSoup4, Pandas, OpenPyXL & SQLite • Deployable on Render
    </div>
    """,
    unsafe_allow_html=True,
)
