"""
Web Scraping Automation Studio
An enterprise-grade, innovative web scraping and data extraction platform.
Theme: Obsidian Sunset & Amber Gold (No Blue).
Features visual extraction modes, pipeline tracker, SQLite audit timeline, and multi-format exports.
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
    page_title="Web Scraping Automation Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize application logger and database
app_logger = setup_logger()
init_db()

# Path to local demo HTML file
DEMO_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo", "demo_page.html")

# ---------------------------------------------------------
# Advanced Custom Styling: Obsidian Sunset & Amber Gold (No Blue)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #F8FAFC;
        }

        /* Hero Title & Branding */
        .hero-banner {
            background: linear-gradient(135deg, rgba(255, 94, 98, 0.1) 0%, rgba(255, 183, 94, 0.05) 50%, rgba(27, 27, 34, 0.8) 100%);
            border: 1px solid rgba(255, 94, 98, 0.25);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 22px;
            position: relative;
            overflow: hidden;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #FF5E62 0%, #FF8C42 40%, #FFB75E 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 6px;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-size: 0.95rem;
            color: #A1A1AA;
            font-weight: 400;
            line-height: 1.5;
        }

        /* Pipeline Stepper Bar */
        .pipeline-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #15151B;
            border: 1px solid #272730;
            border-radius: 12px;
            padding: 12px 18px;
            margin-bottom: 24px;
        }
        .pipeline-step {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            color: #71717A;
        }
        .pipeline-step.active {
            color: #FFB75E;
        }
        .pipeline-step.completed {
            color: #10B981;
        }
        .pipeline-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #3F3F46;
        }
        .pipeline-dot.active {
            background: #FFB75E;
            box-shadow: 0 0 8px #FFB75E;
        }
        .pipeline-dot.completed {
            background: #10B981;
            box-shadow: 0 0 8px #10B981;
        }
        .pipeline-arrow {
            color: #3F3F46;
            font-size: 0.85rem;
        }

        /* Interactive Feature Cards Grid */
        .feature-deck {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-bottom: 24px;
        }
        .mode-card {
            background: #181820;
            border: 1px solid #272732;
            border-radius: 14px;
            padding: 18px 20px;
            transition: all 0.25s ease-in-out;
            cursor: pointer;
            position: relative;
        }
        .mode-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 94, 98, 0.4);
            box-shadow: 0 10px 25px -5px rgba(255, 94, 98, 0.15);
        }
        .mode-card.selected {
            border-color: #FF5E62;
            background: linear-gradient(145deg, #201D24 0%, #17171E 100%);
            box-shadow: 0 8px 20px -4px rgba(255, 94, 98, 0.2);
        }
        .mode-icon {
            font-size: 1.6rem;
            margin-bottom: 8px;
        }
        .mode-title {
            font-size: 1rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 4px;
        }
        .mode-desc {
            font-size: 0.8rem;
            color: #A1A1AA;
            line-height: 1.4;
        }

        /* KPI Cards Ribbon */
        .kpi-deck {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .kpi-box {
            background: linear-gradient(145deg, #1B1B24 0%, #13131A 100%);
            border: 1px solid #262633;
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.35);
            position: relative;
        }
        .kpi-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            border-radius: 14px 14px 0 0;
            background: linear-gradient(90deg, #FF5E62, #FFB75E);
        }
        .kpi-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #A1A1AA;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .kpi-val-amber {
            font-size: 2.2rem;
            font-weight: 800;
            color: #FFB75E;
            line-height: 1;
        }
        .kpi-val-coral {
            font-size: 2.2rem;
            font-weight: 800;
            color: #FF5E62;
            line-height: 1;
        }
        .kpi-val-mint {
            font-size: 1.25rem;
            font-weight: 700;
            color: #10B981;
            line-height: 1.3;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .kpi-val-silver {
            font-size: 1.15rem;
            font-weight: 700;
            color: #E2E8F0;
            line-height: 1.3;
        }

        /* Status Pills */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 14px;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .status-ready {
            background: rgba(161, 161, 170, 0.15);
            color: #E4E4E7;
            border: 1px solid rgba(161, 161, 170, 0.3);
        }
        .status-scraping {
            background: rgba(255, 183, 94, 0.18);
            color: #FFB75E;
            border: 1px solid rgba(255, 183, 94, 0.4);
            animation: pulse-ring 1.5s infinite;
        }
        .status-completed {
            background: rgba(16, 185, 129, 0.18);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .status-failed {
            background: rgba(239, 68, 68, 0.18);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }

        /* Terminal Console */
        .cyber-terminal {
            background-color: #08080C;
            color: #34D399;
            font-family: 'JetBrains Mono', monospace;
            padding: 18px 22px;
            border-radius: 12px;
            border: 1px solid #272732;
            height: 340px;
            overflow-y: auto;
            font-size: 0.85rem;
            line-height: 1.6;
            box-shadow: inset 0 3px 10px rgba(0, 0, 0, 0.7);
        }
        .term-info { color: #38BDF8; }
        .term-success { color: #34D399; font-weight: 600; }
        .term-warning { color: #FFB75E; }
        .term-error { color: #FF5E62; font-weight: 600; }

        /* Sidebar Brand Box */
        .sidebar-brand-box {
            background: linear-gradient(135deg, rgba(255, 94, 98, 0.15) 0%, rgba(255, 183, 94, 0.1) 100%);
            border: 1px solid rgba(255, 94, 98, 0.3);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 20px;
        }
        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #FF8C42;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .sidebar-brand-sub {
            font-size: 0.75rem;
            color: #A1A1AA;
            margin-top: 4px;
        }

        @keyframes pulse-ring {
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
        "type": "Headings",
    }
if "current_logs" not in st.session_state:
    st.session_state.current_logs = [
        "[INFO] Scraping Engine initialized in standby.",
        "[INFO] Select an extraction mode or preset to begin.",
    ]
if "url_input" not in st.session_state:
    st.session_state.url_input = "https://quotes.toscrape.com/"
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Headings"


# ---------------------------------------------------------
# Sidebar Controls & Presets
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand-box">
            <div class="sidebar-brand-title">⚡ Scraping Studio</div>
            <div class="sidebar-brand-sub">Enterprise Extraction & Compliance Engine</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### ⚡ Instant Target Presets")
    demo_selection = st.selectbox(
        "Load Target Preset:",
        [
            "Custom URL...",
            "💬 Quotes to Scrape (Quotes & Tags)",
            "📚 Books to Scrape (Catalog & Prices)",
            "🌐 Wikipedia Countries (Data Matrix)",
            "🧪 Offline Test Bench (Zero Internet)",
        ],
        index=0,
    )

    if demo_selection == "💬 Quotes to Scrape (Quotes & Tags)":
        st.session_state.url_input = "https://quotes.toscrape.com/"
    elif demo_selection == "📚 Books to Scrape (Catalog & Prices)":
        st.session_state.url_input = "https://books.toscrape.com/"
    elif demo_selection == "🌐 Wikipedia Countries (Data Matrix)":
        st.session_state.url_input = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
    elif demo_selection == "🧪 Offline Test Bench (Zero Internet)":
        st.session_state.url_input = "http://demo.local/test-bench"

    st.markdown("---")

    target_url = st.text_input(
        "🌐 Target Website URL",
        value=st.session_state.url_input,
        placeholder="https://example.com",
        help="Enter any public HTTP/HTTPS URL.",
    )
    st.session_state.url_input = target_url

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
        help="Select entity type to extract into clean rows.",
    )
    st.session_state.active_mode = scrape_type

    max_records = st.slider(
        "🔢 Max Record Extraction Cap",
        min_value=5,
        max_value=300,
        value=50,
        step=5,
        help="Maximum records extracted to avoid memory bloating.",
    )

    with st.expander("⚙️ Advanced Network Settings"):
        timeout_seconds = st.slider("HTTP Timeout (seconds)", min_value=3, max_value=30, value=10)
        check_robots = st.checkbox("Strict robots.txt Verification", value=False, help="Checks robots.txt crawling permission before requesting HTML.")
        custom_ua = st.text_input(
            "User-Agent Override",
            value="",
            placeholder="Default Chrome agent",
            help="Custom user-agent string.",
        )

    st.markdown("---")

    col_b1, col_b2 = st.columns(2)
    start_clicked = col_b1.button("🚀 Start Scraping", type="primary", use_container_width=True)
    clear_clicked = col_b2.button("🔄 Reset View", use_container_width=True)

    if clear_clicked:
        st.session_state.scraped_data = None
        st.session_state.scrape_status = "Ready"
        st.session_state.error_message = None
        st.session_state.scrape_stats = {
            "records": 0,
            "time": 0.0,
            "url": "None",
            "timestamp": "Never",
            "type": "Headings",
        }
        st.session_state.current_logs = [
            "[INFO] Canvas cleared.",
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
        save_history(
            url=result.url,
            scrape_type=result.scrape_type,
            record_count=result.record_count,
            status="Success",
            execution_time=result.execution_time,
            preview_df=result.data,
        )
    elif result.success and (result.data is None or result.data.empty):
        st.session_state.scrape_status = "Completed"
        st.session_state.scraped_data = pd.DataFrame()
        st.session_state.error_message = result.error_message or f"ℹ️ 0 {scrape_type} records found on this webpage."
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
        save_history(
            url=result.url,
            scrape_type=result.scrape_type,
            record_count=0,
            status="Failed",
            execution_time=result.execution_time,
            error_message=result.error_message,
        )


# ---------------------------------------------------------
# Top Section: Hero Banner & Status
# ---------------------------------------------------------
col_banner_left, col_banner_right = st.columns([3, 1])

with col_banner_left:
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-title">⚡ Web Scraping Automation Studio</div>
            <div class="hero-subtitle">
                Automated Web Data Mining, Ethical Compliance Auditing & Multi-Format Analytical Export Engine
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_banner_right:
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
        <div style="background: #181820; border: 1px solid #272732; border-radius: 14px; padding: 18px 20px; text-align: center; margin-top: 4px;">
            <div style="color: #A1A1AA; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 8px;">ENGINE STATUS</div>
            <div class="status-pill {badge_cls}">{icon} {status_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Section 1: Live Pipeline Stepper Visualizer
# ---------------------------------------------------------
step1_cls = "completed" if st.session_state.scrape_status in ("Completed", "Scraping...") else "active"
step2_cls = "completed" if st.session_state.scrape_status == "Completed" else ("active" if st.session_state.scrape_status == "Scraping..." else "")
step3_cls = "completed" if st.session_state.scrape_status == "Completed" else ""
step4_cls = "completed" if st.session_state.scrape_status == "Completed" else ""

st.markdown(
    f"""
    <div class="pipeline-container">
        <div class="pipeline-step {step1_cls}">
            <div class="pipeline-dot {step1_cls}"></div>
            <span>1. Schema & SSRF Guard</span>
        </div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step {step2_cls}">
            <div class="pipeline-dot {step2_cls}"></div>
            <span>2. robots.txt Verification</span>
        </div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step {step2_cls}">
            <div class="pipeline-dot {step2_cls}"></div>
            <span>3. HTTP Handshake</span>
        </div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step {step3_cls}">
            <div class="pipeline-dot {step3_cls}"></div>
            <span>4. DOM Parse & Deduplication</span>
        </div>
        <div class="pipeline-arrow">➔</div>
        <div class="pipeline-step {step4_cls}">
            <div class="pipeline-dot {step4_cls}"></div>
            <span>5. Tabular Data Ready</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Section 2: Innovative Extraction Modes Grid
# ---------------------------------------------------------
st.markdown("##### 🎯 Supported Extraction Engines")
col_card1, col_card2, col_card3 = st.columns(3)

with col_card1:
    h_selected = "selected" if st.session_state.active_mode == "Headings" else ""
    st.markdown(
        f"""
        <div class="mode-card {h_selected}">
            <div class="mode-icon">🏷️</div>
            <div class="mode-title">Headings Architecture</div>
            <div class="mode-desc">Extracts visual H1–H6 hierarchy with level tags and character counts for SEO audits.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_card2:
    l_selected = "selected" if st.session_state.active_mode == "Links" else ""
    st.markdown(
        f"""
        <div class="mode-card {l_selected}">
            <div class="mode-icon">🔗</div>
            <div class="mode-title">Hyperlink Harvester</div>
            <div class="mode-desc">Resolves relative paths to absolute URLs and classifies internal vs external domain links.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_card3:
    t_selected = "selected" if st.session_state.active_mode == "Tables" else ""
    st.markdown(
        f"""
        <div class="mode-card {t_selected}">
            <div class="mode-icon">📊</div>
            <div class="mode-title">Tabular Data Matrix</div>
            <div class="mode-desc">Auto-synthesizes missing headers, pads irregular rows, and normalizes table grids into DataFrames.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

col_card4, col_card5, col_card6 = st.columns(3)
with col_card4:
    p_selected = "selected" if st.session_state.active_mode == "Paragraphs" else ""
    st.markdown(
        f"""
        <div class="mode-card {p_selected}">
            <div class="mode-icon">📝</div>
            <div class="mode-title">Content & Prose Miner</div>
            <div class="mode-desc">Eliminates excess whitespace, filters empty tags, and calculates word & character density.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_card5:
    m_selected = "selected" if st.session_state.active_mode == "Page Title" else ""
    st.markdown(
        f"""
        <div class="mode-card {m_selected}">
            <div class="mode-icon">🌐</div>
            <div class="mode-title">Meta & OpenGraph</div>
            <div class="mode-desc">Captures document titles, meta descriptions, and canonical URLs for metadata governance.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_card6:
    i_selected = "selected" if st.session_state.active_mode == "Images" else ""
    st.markdown(
        f"""
        <div class="mode-card {i_selected}">
            <div class="mode-icon">🖼️</div>
            <div class="mode-title">Media Asset Collector</div>
            <div class="mode-desc">Extracts normalized image sources, alt text descriptions, and filters data-URI placeholders.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Section 3: Executive KPI Deck
# ---------------------------------------------------------
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown(
        f"""
        <div class="kpi-box">
            <div class="kpi-label">📊 Records Captured</div>
            <div class="kpi-val-amber">{st.session_state.scrape_stats['records']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        f"""
        <div class="kpi-box">
            <div class="kpi-label">⚡ Execution Latency</div>
            <div class="kpi-val-coral">{st.session_state.scrape_stats['time']:.2f}s</div>
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
        <div class="kpi-box">
            <div class="kpi-label">🌐 Target Host</div>
            <div class="kpi-val-mint" title="{domain_display}">{domain_display}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m4:
    last_time = st.session_state.scrape_stats['timestamp']
    display_time = last_time.split(' ')[-1] if last_time != "Never" else "Never"
    st.markdown(
        f"""
        <div class="kpi-box">
            <div class="kpi-label">🕒 Timestamp</div>
            <div class="kpi-val-silver">{display_time}</div>
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
# Section 4: Interactive Workspace Tabs
# ---------------------------------------------------------
tab_data, tab_logs, tab_history, tab_robots, tab_demo, tab_guide = st.tabs([
    "📊 Scraped Data Studio",
    "⚡ Realtime Telemetry",
    "🗄️ SQLite Audit Timeline",
    "🛡️ Compliance & robots.txt",
    "🧪 Zero-Internet Test Bench",
    "💡 Interviewer Guide & Architecture",
])

# ---------------------------------------------------------
# Tab 1: Scraped Data Studio
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
                f"<div style='text-align: right; padding-top: 8px; color: #FFB75E; font-weight: 700; font-size: 0.9rem;'>"
                f"✅ Extracted {len(df_current):,} Rows × {len(df_current.columns)} Columns"
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
        st.info("👋 Studio is ready. Enter a target URL in the sidebar or pick an instant preset, then click **'🚀 Start Scraping'**.")


# ---------------------------------------------------------
# Tab 2: Realtime Telemetry
# ---------------------------------------------------------
with tab_logs:
    col_log_head, col_log_clear = st.columns([5, 1])
    col_log_head.markdown("#### ⚡ Network & Extraction Event Stream")
    if col_log_clear.button("Clear Log Stream", use_container_width=True):
        st.session_state.current_logs = ["[INFO] Telemetry stream cleared."]
        st.rerun()

    log_html_lines = []
    for line in st.session_state.current_logs:
        if "[ERROR]" in line:
            cls = "term-error"
        elif "[WARNING]" in line:
            cls = "term-warning"
        elif "[SUCCESS]" in line:
            cls = "term-success"
        else:
            cls = "term-info"
        log_html_lines.append(f"<div class='{cls}'>{line}</div>")

    st.markdown(
        f"""
        <div class="cyber-terminal">
            {''.join(log_html_lines)}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Telemetry traces network DNS handshake, HTTP status validation, DOM parsing, and deduplication passes.")


# ---------------------------------------------------------
# Tab 3: SQLite Audit Timeline
# ---------------------------------------------------------
with tab_history:
    st.markdown("#### 🗄️ Relational Audit Timeline (SQLite)")

    db_stats = get_stats()
    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    col_h1.metric("Cumulative Jobs", db_stats["total_scrapes"])
    col_h2.metric("Successful Scrapes", db_stats["successful"])
    col_h3.metric("Success Rate", f"{db_stats['success_rate']}%")
    col_h4.metric("Total Records Saved", f"{db_stats['total_records']:,}")

    st.markdown("---")

    col_f1, col_f2, col_f3 = st.columns([3, 2, 1])
    search_term = col_f1.text_input("🔍 Search History by Keyword or Domain", placeholder="e.g. quotes, books, headings...")
    status_sel = col_f2.selectbox("Filter Job Status", ["All", "Success", "Failed"])

    if col_f3.button("🗑️ Wipe History", use_container_width=True, help="Permanently clear SQLite history database"):
        clear_history()
        st.success("History database wiped cleanly.")
        st.rerun()

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

        st.markdown("##### 🔎 Stored Snapshot Inspector")
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
# Tab 4: Compliance & robots.txt
# ---------------------------------------------------------
with tab_robots:
    st.markdown("#### 🛡️ Compliance & robots.txt Protocol Auditor")
    st.write(
        "Ethical web data extraction requires compliance with the target site's Robots Exclusion Standard (`/robots.txt`). "
        "Test any target URL to verify whether automated crawling is permitted."
    )

    col_r1, col_r2 = st.columns([3, 1])
    test_url = col_r1.text_input("Enter URL to audit:", value=st.session_state.url_input)
    audit_clicked = col_r2.button("🔍 Run Compliance Audit", use_container_width=True)

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
# Tab 5: Zero-Internet Test Bench
# ---------------------------------------------------------
with tab_demo:
    st.markdown("#### 🧪 Zero-Dependency Offline Test Bench")
    st.write(
        "Demonstrate the scraper in an environment with unstable Wi-Fi or firewall restrictions. "
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
            st.success(f"Successfully extracted {result.record_count} records from the offline test bench! Check the '📊 Scraped Data Studio' tab.")
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
    <div style="text-align: center; color: #71717A; font-size: 0.85rem; padding: 15px 0;">
        <span style="color: #FF8C42; font-weight: 700;">Web Scraping Automation Studio</span> • Production & Interview Ready<br>
        Engineered with Python 3.12, Streamlit, Requests, BeautifulSoup4, Pandas, OpenPyXL & SQLite • Hosted on Render
    </div>
    """,
    unsafe_allow_html=True,
)
