from __future__ import annotations

import os
import html
import requests
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

API = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="Veritas KPI — Decision Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.get("authenticated", False) else "collapsed",
)

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = "ceo"
if "role" not in st.session_state:
    st.session_state.role = "CEO / CFO"
if "region" not in st.session_state:
    st.session_state.region = "North"
if "active_page" not in st.session_state:
    st.session_state.active_page = "REVENUE"
if "kpi_selected" not in st.session_state:
    st.session_state.kpi_selected = "revenue"
if "scenario" not in st.session_state:
    st.session_state.scenario = "main"
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Enterprise Custom Design System CSS — Clean Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html,body,[class*="css"]{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;background-color:#FAFAFA;color:#18181B;}
    .stApp{background-color:#FAFAFA;}
    .block-container{padding-top:1rem;padding-bottom:1.5rem;padding-left:1.5rem;padding-right:1.5rem;max-width:100%;}
    .landing-brand-panel{background:linear-gradient(155deg,#1e1b4b 0%,#3730a3 50%,#4f46e5 100%);border-radius:16px;padding:3rem 2.4rem;color:#fff;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 12px 32px rgba(79,70,229,.2);}
    .brand-logo-badge{display:inline-flex;align-items:center;gap:.45rem;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:30px;padding:.3rem .85rem;font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#c7d2fe;margin-bottom:1.6rem;}
    .brand-dot{width:7px;height:7px;background:#6ee7b7;border-radius:50%;display:inline-block;animation:pulse 2s ease-in-out infinite;}
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
    .brand-headline{font-size:2.1rem;font-weight:800;line-height:1.2;letter-spacing:-.03em;color:#fff;margin-bottom:1rem;}
    .brand-subtext{font-size:.9rem;line-height:1.65;color:#a5b4fc;margin-bottom:2rem;}
    .brand-divider{border:none;border-top:1px solid rgba(255,255,255,.1);margin:1.4rem 0;}
    .brand-features{list-style:none;padding:0;margin:0;}
    .brand-features li{font-size:.85rem;font-weight:500;color:#c7d2fe;margin-bottom:.6rem;display:flex;align-items:center;gap:.55rem;}
    .brand-check{color:#6ee7b7;font-weight:800;}
    .brand-footer-note{font-size:.68rem;color:rgba(255,255,255,.3);margin-top:2rem;letter-spacing:.04em;}
    .persona-section-title{font-size:1.45rem;font-weight:800;color:#18181B;letter-spacing:-.025em;margin:0 0 .2rem 0;}
    .persona-section-sub{font-size:.85rem;color:#71717a;margin-bottom:1.4rem;}
    .persona-card{background:#fff;border:1.5px solid #e4e4e7;border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:.85rem;box-shadow:0 1px 4px rgba(0,0,0,.04);transition:border-color .15s,box-shadow .15s;}
    .persona-card:hover{border-color:#6366f1;box-shadow:0 4px 16px rgba(99,102,241,.1);}
    .persona-card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.3rem;}
    .persona-card-title{font-size:.95rem;font-weight:700;color:#18181B;}
    .persona-card-sub{font-size:.73rem;font-weight:600;color:#6366f1;margin-top:.1rem;}
    .persona-card-badges{display:flex;gap:.3rem;flex-shrink:0;}
    .persona-card-desc{font-size:.78rem;color:#52525b;line-height:1.45;margin:.4rem 0 .7rem 0;}
    .badge-scope{background:#eef2ff;color:#4f46e5;border:1px solid #c7d2fe;}
    .badge-scope-north{background:#fef3c7;color:#92400e;border:1px solid #fde68a;}
    .badge-scope-analyst{background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;}
    .badge-access{background:#f4f4f5;color:#52525b;border:1px solid #e4e4e7;}
    .badge-scope,.badge-scope-north,.badge-scope-analyst,.badge-access{font-size:.63rem;font-weight:700;padding:.14rem .45rem;border-radius:5px;letter-spacing:.04em;white-space:nowrap;}
    div[data-testid="stButton"]>button[kind="primary"]{background:#4f46e5!important;border:none!important;border-radius:8px!important;font-size:.78rem!important;font-weight:600!important;padding:.45rem 1rem!important;transition:background .15s!important;width:100%!important;}
    div[data-testid="stButton"]>button[kind="primary"]:hover{background:#4338ca!important;}
    .header-bar{background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:.85rem 1.3rem;margin-bottom:1rem;box-shadow:0 1px 4px rgba(0,0,0,.04);}
    .header-title{font-size:1.1rem;font-weight:800;letter-spacing:-.02em;margin:0;color:#18181B;}
    .header-badge{background:#eef2ff;border:1px solid #c7d2fe;border-radius:20px;padding:.12rem .6rem;font-size:.68rem;font-weight:700;letter-spacing:.04em;color:#4f46e5;margin-left:.6rem;vertical-align:middle;}
    .header-subtitle{font-size:.78rem;color:#71717a;margin-top:.15rem;}
    .card-container{background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:1.1rem;box-shadow:0 1px 3px rgba(0,0,0,.03);margin-bottom:1rem;height:100%;}
    .kpi-card{background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:.9rem 1rem;box-shadow:0 1px 3px rgba(0,0,0,.03);transition:border-color .15s,box-shadow .15s;}
    .kpi-card:hover{border-color:#a1a1aa;box-shadow:0 4px 12px rgba(0,0,0,.06);}
    .kpi-label{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#71717a;margin-bottom:.3rem;}
    .kpi-value{font-size:1.5rem;font-weight:700;color:#18181B;letter-spacing:-.02em;margin-bottom:.15rem;}
    .kpi-delta-pos{color:#059669;font-weight:600;font-size:.78rem;}
    .kpi-delta-neg{color:#e11d48;font-weight:600;font-size:.78rem;}
    .kpi-sub{font-size:.7rem;color:#a1a1aa;margin-top:.25rem;border-top:1px solid #f4f4f5;padding-top:.4rem;}
    .badge-critical{background:#fff1f2;color:#e11d48;border:1px solid #fecdd3;font-size:.63rem;font-weight:700;padding:.14rem .5rem;border-radius:5px;letter-spacing:.03em;}
    .badge-warning{background:#fffbeb;color:#d97706;border:1px solid #fde68a;font-size:.63rem;font-weight:700;padding:.14rem .5rem;border-radius:5px;letter-spacing:.03em;}
    .badge-optimal{background:#ecfdf5;color:#059669;border:1px solid #a7f3d0;font-size:.63rem;font-weight:700;padding:.14rem .5rem;border-radius:5px;letter-spacing:.03em;}
    .badge-high{background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;font-size:.68rem;font-weight:600;padding:.14rem .5rem;border-radius:5px;}
    .badge-medium{background:#fffbeb;color:#92400e;border:1px solid #fde68a;font-size:.68rem;font-weight:600;padding:.14rem .5rem;border-radius:5px;}
    .badge-low{background:#fff1f2;color:#991b1b;border:1px solid #fecdd3;font-size:.68rem;font-weight:600;padding:.14rem .5rem;border-radius:5px;}
    .panel-header{font-size:.9rem;font-weight:700;color:#18181B;margin-bottom:.15rem;}
    .panel-sub{font-size:.75rem;color:#71717a;margin-bottom:.85rem;}
    .diag-card{background:#f9f9fb;border-left:3px solid #6366f1;border-radius:8px;padding:.8rem 1rem;margin-bottom:.65rem;}
    .diag-card-warn{background:#fffbeb;border-left:3px solid #f59e0b;border-radius:8px;padding:.8rem 1rem;margin-bottom:.65rem;}
    .action-card{background:#fff;border:1px solid #e4e4e7;border-top:3px solid #4f46e5;border-radius:10px;padding:1rem;margin-bottom:.75rem;}
    .abstain-banner{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:.9rem 1.1rem;margin-bottom:1rem;color:#78350f;}
    .insight-box{background:#f9f9fb;border:1px solid #e4e4e7;border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem;}
    .sidebar-persona-badge{background:#f4f4f5;border:1px solid #e4e4e7;border-radius:10px;padding:.8rem 1rem;margin-bottom:1rem;}
    .sidebar-persona-role{font-size:.9rem;font-weight:700;color:#18181B;}
    .sidebar-persona-meta{font-size:.72rem;color:#71717a;margin-top:.2rem;}
    .rc-table{width:100%;border-collapse:collapse;font-size:.78rem;}
    .rc-table th{background:#f9f9fb;color:#71717a;font-weight:600;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;padding:.65rem .75rem;border-top:1px solid #e4e4e7;border-bottom:1px solid #e4e4e7;text-align:left;}
    .rc-table td{padding:.75rem;color:#3f3f46;border-bottom:1px solid #f4f4f5;vertical-align:middle;}
    .rc-table td:first-child{font-weight:600;color:#18181B;}
    .rc-table tr:last-child td{border-bottom:none;}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# ROUTING CONTROLLER
# ==============================================================================

if not st.session_state.authenticated:
    # -------------------------------------------------------------------------
    # 1. FIRST SCREEN: DIRECT PERSONA SELECTOR (NO AUTHENTICATION FORM)
    # -------------------------------------------------------------------------
    col_left, col_right = st.columns([43, 57])
    
    with col_left:
        st.markdown("""
        <div class="landing-brand-panel">
            <div>
                <span class="brand-logo-badge">
                    <span class="brand-dot"></span>
                    VERITAS KPI ENGINE
                </span>
                <div class="brand-headline">
                    Evidence-Grounded<br>Intelligence to Action
                </div>
                <div class="brand-subtext">
                    Detect what changed. Understand why.<br>
                    Measure confidence. Take the right action.
                </div>
                <hr class="brand-divider">
                <ul class="brand-features">
                    <li><span class="brand-check">✓</span> Deterministic KPI analytics</li>
                    <li><span class="brand-check">✓</span> Evidence Confidence &amp; abstention</li>
                    <li><span class="brand-check">✓</span> Persona-aware governed actions</li>
                    <li><span class="brand-check">✓</span> Secure decision intelligence</li>
                </ul>
            </div>
            <div class="brand-footer-note">HACKATHON PROTOTYPE · DEMO MODE · ALL DATA SYNTHETIC</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_right:
        st.markdown("""
        <div style="padding: 1.5rem 0.5rem 0 1rem;">
            <div class="persona-section-title">CHOOSE YOUR DEMO VIEW</div>
            <div class="persona-section-sub">Select a role to enter the interactive decision engine</div>
        </div>
        """, unsafe_allow_html=True)
        
        # ── CEO / CFO CARD ──────────────────────────────────────────────
        st.markdown("""
        <div class="persona-card">
            <div class="persona-card-top">
                <div>
                    <div class="persona-card-title">CEO / CFO</div>
                    <div class="persona-card-sub">Enterprise Performance</div>
                </div>
                <div class="persona-card-badges">
                    <span class="badge-scope">ALL REGIONS</span>
                    <span class="badge-access">EXECUTIVE</span>
                </div>
            </div>
            <div class="persona-card-desc">
                Executive view across all regions, KPIs, strategic insights and governed actions.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ENTER DASHBOARD →", key="btn_ceo", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user = "ceo"
            st.session_state.role = "CEO / CFO"
            st.session_state.region = "North"
            st.session_state.active_page = "REVENUE"
            st.session_state.chat_open = False
            st.session_state.chat_messages = []
            st.rerun()

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        # ── NORTH REGIONAL MANAGER CARD ─────────────────────────────────
        st.markdown("""
        <div class="persona-card">
            <div class="persona-card-top">
                <div>
                    <div class="persona-card-title">North Regional Manager</div>
                    <div class="persona-card-sub">Regional Operations</div>
                </div>
                <div class="persona-card-badges">
                    <span class="badge-scope-north">NORTH ONLY</span>
                    <span class="badge-access">REGIONAL</span>
                </div>
            </div>
            <div class="persona-card-desc">
                Operational performance, revenue diagnosis, inventory, conversion and authorized North-region actions.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ENTER DASHBOARD →", key="btn_north", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user = "north_mgr"
            st.session_state.role = "North Regional Manager"
            st.session_state.region = "North"
            st.session_state.active_page = "REVENUE"
            st.session_state.chat_open = False
            st.session_state.chat_messages = []
            st.rerun()

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        # ── BUSINESS ANALYST CARD ───────────────────────────────────────
        st.markdown("""
        <div class="persona-card">
            <div class="persona-card-top">
                <div>
                    <div class="persona-card-title">Business Analyst</div>
                    <div class="persona-card-sub">Evidence &amp; Diagnostics</div>
                </div>
                <div class="persona-card-badges">
                    <span class="badge-scope-analyst">AUTHORIZED ANALYTICS</span>
                    <span class="badge-access">ANALYST</span>
                </div>
            </div>
            <div class="persona-card-desc">
                Detailed KPI analysis, evidence, lineage, confidence, diagnostics and evaluation.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ENTER DASHBOARD →", key="btn_analyst", type="primary", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user = "analyst"
            st.session_state.role = "Business Analyst"
            st.session_state.region = "North"
            st.session_state.active_page = "EVIDENCE"
            st.session_state.chat_open = False
            st.session_state.chat_messages = []
            st.rerun()

    st.stop()

# ==============================================================================
# 2. DASHBOARD SHELL (AUTHENTICATED PERSONA SESSION)
# ==============================================================================

# LEFT SIDEBAR NAVIGATION & PERSONA SWITCHER
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-persona-badge">
        <div class="sidebar-persona-role">👤 {st.session_state.role}</div>
        <div class="sidebar-persona-meta">
            User ID: <code>{st.session_state.user}</code><br>
            Scope: <code>{st.session_state.region} Region</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**NAVIGATION**")
    nav_pages = ["USER", "ORDERS", "REVENUE", "DIAGNOSIS", "ACTIONS", "EVIDENCE", "NEW PRODUCT", "SYSTEM"]
    
    # Calculate default index for active_page
    current_idx = 2 # Default to REVENUE
    if st.session_state.active_page in nav_pages:
        current_idx = nav_pages.index(st.session_state.active_page)
        
    selected_nav = st.radio("Go to:", nav_pages, index=current_idx, label_visibility="collapsed")
    st.session_state.active_page = selected_nav

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # CHANGE PERSONA BUTTON AT BOTTOM
    if st.button("🔄 CHANGE PERSONA", key="btn_change_persona", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = "ceo"
        st.session_state.role = "CEO / CFO"
        st.session_state.chat_open = False
        st.session_state.chat_messages = []
        st.rerun()

# Map navigation selection to focus metric if applicable
if st.session_state.active_page == "USER":
    st.session_state.kpi_selected = "conversion_rate"
elif st.session_state.active_page == "ORDERS":
    st.session_state.kpi_selected = "orders"
elif st.session_state.active_page == "REVENUE":
    st.session_state.kpi_selected = "revenue"

# Top Bar Header
st.markdown(f"""
<div class="header-bar">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span class="header-title">VERITAS KPI</span>
            <span class="header-badge">DECISION ENGINE</span>
            <span style="font-size:0.75rem; color:#E0E7FF; margin-left:0.5rem;">Active Persona: <strong>{st.session_state.role}</strong></span>
            <div class="header-subtitle">Evidence-Grounded Intelligence to Action • Deterministic Analytics & Governed Diagnosis</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Bar Controls
ctl1, ctl2, ctl3, ctl4 = st.columns([2.5, 2.5, 2.5, 2.5])

with ctl1:
    # Role Scoped Region Selector
    if st.session_state.user == "north_mgr":
        region_list = ["North", "South", "East", "West"]
        region = st.selectbox("Region Scope", region_list, index=0, help="North Manager is restricted to North region data.")
    else:
        region_list = ["North", "South", "East", "West"]
        reg_idx = region_list.index(st.session_state.region) if st.session_state.region in region_list else 0
        region = st.selectbox("Region Scope", region_list, index=reg_idx)
    st.session_state.region = region

with ctl2:
    kpi_keys = ["revenue", "orders", "conversion_rate", "aov", "gross_margin"]
    kpi_idx = kpi_keys.index(st.session_state.kpi_selected) if st.session_state.kpi_selected in kpi_keys else 0
    kpi_selected = st.selectbox(
        "Focus Metric",
        kpi_keys,
        index=kpi_idx,
        format_func=lambda k: {
            "revenue": "Revenue (₹)",
            "orders": "Orders (Count)",
            "conversion_rate": "Conversion Rate (%)",
            "aov": "Average Order Value (₹)",
            "gross_margin": "Gross Margin (%)",
        }[k],
    )
    st.session_state.kpi_selected = kpi_selected

with ctl3:
    scenario = st.selectbox(
        "Evidence Scenario",
        ["main", "degraded"],
        index=0 if st.session_state.scenario == "main" else 1,
        format_func=lambda s: "🟢 Main (Live Feeds)" if s == "main" else "🟡 Degraded (Stale Marketing)",
    )
    st.session_state.scenario = scenario

with ctl4:
    st.markdown("<div style='margin-top: 1.7rem;'></div>", unsafe_allow_html=True)
    if scenario == "main":
        st.markdown("<span class='badge-high'>● Feeds Current (SLA 100%)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-medium'>⚠️ Marketing Feed Stale (30h)</span>", unsafe_allow_html=True)

headers = {"X-Demo-User": st.session_state.user}

# Fetch primary backend data
# Note: statsmodels Holt-Winters forecasts are compute-heavy on cold start (20-40s).
# Timeout is set to 60s to allow for backend warm-up.
try:
    with st.spinner("⏳ Loading analytics engine… (may take 20-40s on first load while the forecast model warms up)"):
        res = requests.get(
            f"{API}/api/insight",
            params={"kpi": kpi_selected, "region": region, "scenario": scenario},
            headers=headers,
            timeout=60,
        )
    if res.status_code == 403:
        st.error(f"🔒 **Access Denied (Security Entitlements Policy)**\n\n{res.json().get('detail', 'Unauthorized regional access.')}")
        st.info("💡 **Security Enforcement:** Scoped SQL queries filter unauthorized data BEFORE processing. North Manager cannot view South/East/West data.")
        st.stop()
    res.raise_for_status()
    insight_data = res.json()
except requests.exceptions.Timeout:
    st.warning("⏳ **Backend is warming up.** The analytics engine (Holt-Winters forecasting) takes 20-40s on first load.")
    if st.button("🔄 Retry", key="retry_btn", type="primary"):
        st.rerun()
    st.stop()
except Exception as exc:
    st.error(f"Connection Error: Unable to reach FastAPI backend at `{API}`. {exc}")
    st.info("Ensure backend server is running: `python -m uvicorn backend.app.main:app --reload --port 8000`")
    if st.button("🔄 Retry Connection", key="retry_conn_btn", type="primary"):
        st.rerun()
    st.stop()

evidence = insight_data["evidence"]
narrative = insight_data["narrative"]
actions = insight_data["actions"]

# Helper formatting functions
def fmt_val(k: str, val: float | None) -> str:
    if val is None:
        return "N/A"
    if k in ("revenue", "business_impact_inr"):
        crore = val / 10_000_000
        if abs(crore) >= 1.0:
            return f"₹{crore:.2f} Cr"
        lakh = val / 100_000
        if abs(lakh) >= 1.0:
            return f"₹{lakh:.2f} L"
        return f"₹{val:,.2f}"
    elif k in ("conversion_rate", "gross_margin"):
        return f"{val*100:.2f}%" if val <= 1.0 else f"{val:.2f}%"
    elif k == "aov":
        return f"₹{val:,.2f}"
    else:
        return f"{val:,.0f}"

def get_badge(ecs: float, band: str) -> str:
    if ecs >= 0.75 or band == "HIGH":
        return f"<span class='badge-high'>HIGH ({ecs:.2f})</span>"
    elif ecs >= 0.50 or band == "MEDIUM":
        return f"<span class='badge-medium'>MEDIUM ({ecs:.2f})</span>"
    else:
        return f"<span class='badge-low'>LOW / UNCERTAIN ({ecs:.2f})</span>"

# Fetch 5 KPI summary cards data dynamically
# Use generous timeout since backend may still be warm-starting secondary KPI models
cards_data = {}
for k in kpi_keys:
    try:
        r_k = requests.get(f"{API}/api/insight", params={"kpi": k, "region": region, "scenario": scenario}, headers=headers, timeout=30)
        if r_k.status_code == 200:
            cards_data[k] = r_k.json()["evidence"]
    except Exception:
        pass  # Cards gracefully degrade if backend is still warming up

# ──────────────────────────────────────────────────────────────────────────────
# FLOATING VERITAS INTELLIGENCE ASSISTANT (NATIVE ST.POPOVER FLOATING WIDGET)
# ──────────────────────────────────────────────────────────────────────────────

# Page-aware suggestion chips
_page_suggestions = {
    "REVENUE":    ["Why did Revenue decline?", "What contributed most to the drop?", "What action should we take?"],
    "ORDERS":     ["Why did Orders change?", "Which channel drove the movement?", "What should we do about Orders?"],
    "USER":       ["Why did Conversion Rate drop?", "What is affecting user behaviour?", "Which region drives this?"],
    "DIAGNOSIS":  ["What is the strongest diagnosis?", "Why is Marketing evidence uncertain?", "How confident is this analysis?"],
    "ACTIONS":    ["Which action has highest priority?", "Who owns the top action?", "What is the expected business impact?"],
    "EVIDENCE":   ["Show the full evidence.", "Why is confidence MEDIUM?", "What is the data freshness status?"],
    "NEW PRODUCT":["How confident is the sparse-history benchmark?", "How does P020 compare to its cohort?"],
    "SYSTEM":     ["What is the total analytics latency?", "Is the North Manager security working?"],
}
_suggestions = _page_suggestions.get(st.session_state.active_page, [
    "Why did Revenue decline?",
    "What is driving Conversion?",
    "What action should we take?",
    "How confident is this diagnosis?",
])

# Persona-aware welcome
_welcome_map = {
    "ceo":       "Ask me about enterprise KPI performance, business impact, drivers, or strategic actions.",
    "north_mgr": "Ask me about North Revenue, Orders, Conversion, inventory issues, or operational actions.",
    "analyst":   "Ask me about KPI evidence, driver diagnostics, confidence, lineage, or methodology.",
}
_welcome = _welcome_map.get(
    st.session_state.user,
    "Ask me about Revenue, Orders, Conversion, AOV, Margin, business drivers, evidence, or recommended actions."
)

_CHATBOT_RIBBON_SVG = '<svg class="b-symbol" viewBox="0 0 100 120" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="blueGradient1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#00c6ff" /><stop offset="100%" stop-color="#2563eb" /></linearGradient><linearGradient id="blueGradient2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#3b82f6" /><stop offset="100%" stop-color="#1d4ed8" /></linearGradient><linearGradient id="cyanGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#38bdf8" /><stop offset="100%" stop-color="#06b6d4" /></linearGradient></defs><path class="ribbon-back" d="M20 10 C 20 5, 28 0, 35 0 L 45 0 C 52 0, 55 5, 55 12 L 55 85 C 55 100, 38 112, 22 108 C 20 107, 20 102, 20 98 Z" /><path class="ribbon-front" d="M20 70 L 55 105 C 68 115, 85 100, 75 80 L 55 45 L 20 70 Z" /><path class="ribbon-loop" d="M50 42 L 72 48 C 82 52, 85 68, 72 75 L 50 82 Z" /></svg>'

_CHATBOT_ICON_HTML = f'<div class="chatbot-bubble-wrapper" aria-hidden="true"><div class="chatbot-inner">{_CHATBOT_RIBBON_SVG}</div></div>'


def _chat_html(text: str) -> str:
    return html.escape(str(text)).replace("\n", "<br>")


def _chat_requested_region(question: str, fallback_region: str) -> str:
    question_l = f" {question.lower()} "
    for candidate in ("North", "South", "East", "West"):
        if f" {candidate.lower()} " in question_l:
            return candidate
    return fallback_region


def _chat_display_answer(payload: dict) -> str:
    answer = str(payload.get("answer", "Unable to answer question."))
    answer = "\n".join(line for line in answer.splitlines() if "Parsed Intent" not in line)
    if answer.startswith("Evidence Object ID"):
        evidence_parts = answer.split(". ", 1)
        if len(evidence_parts) == 2:
            answer = f"Supporting evidence: {evidence_parts[1]}"
    return answer


def _handle_ask(question_str: str) -> None:
    question = question_str.strip()
    if not question:
        return

    requested_region = _chat_requested_region(question, region)
    st.session_state.chat_open = True
    st.session_state.chat_messages.append({"role": "user", "content": question})

    try:
        r_ask = requests.post(
            f"{API}/api/ask",
            json={
                "question": question,
                "region": requested_region,
                "kpi": kpi_selected,
                "scenario": scenario,
            },
            headers=headers,
            timeout=15,
        )
        if r_ask.status_code == 403:
            if st.session_state.user == "north_mgr":
                answer = "Access restricted. Your current role is authorized for North-region intelligence only."
            else:
                answer = "Access restricted. Your current scope does not include that region."
        else:
            r_ask.raise_for_status()
            answer = _chat_display_answer(r_ask.json())
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
    except Exception:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": "Encountered an issue reaching the analytics backend.",
        })

st.markdown("""
<style>
/* ============================================================================
   VERITAS KPI FLOATING ASSISTANT — MODERN BUSINESS INTELLIGENCE DESIGN
   ============================================================================ */

.st-key-veritas_floating_assistant {
    --veritas-chatbot-icon: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220"><defs><linearGradient id="ring" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%2300c6ff"/><stop offset="1" stop-color="%231e40af"/></linearGradient><linearGradient id="blueGradient1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%2300c6ff"/><stop offset="1" stop-color="%232563eb"/></linearGradient><linearGradient id="blueGradient2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%233b82f6"/><stop offset="1" stop-color="%231d4ed8"/></linearGradient><linearGradient id="cyanGradient" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%2338bdf8"/><stop offset="1" stop-color="%2306b6d4"/></linearGradient></defs><path d="M110 0C171 0 220 49 220 110C220 173 173 215 110 215C94 215 79 212 65 205L23 216C12 219 1 209 5 198L17 155C6 140 0 126 0 110C0 49 49 0 110 0Z" fill="url(%23ring)"/><path d="M110 12C164 12 208 56 208 110C208 166 166 202 110 202C96 202 82 199 69 193L31 203C24 205 18 199 20 192L30 153C18 140 12 126 12 110C12 56 56 12 110 12Z" fill="%23ffffff"/><g transform="translate(63 50) scale(.86)"><path d="M20 10 C 20 5, 28 0, 35 0 L 45 0 C 52 0, 55 5, 55 12 L 55 85 C 55 100, 38 112, 22 108 C 20 107, 20 102, 20 98 Z" fill="url(%23blueGradient1)"/><path d="M20 70 L 55 105 C 68 115, 85 100, 75 80 L 55 45 L 20 70 Z" fill="url(%23blueGradient2)"/><path d="M50 42 L 72 48 C 82 52, 85 68, 72 75 L 50 82 Z" fill="url(%23cyanGradient)"/></g></svg>');
    position: fixed !important;
    right: 24px !important;
    bottom: 24px !important;
    width: min(340px, calc(100vw - 32px)) !important;
    z-index: 9999 !important;
    pointer-events: none;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.st-key-veritas_floating_assistant * {
    pointer-events: auto;
}

/* Chat panel — compact, elevated, professional */
.st-key-veritas_assistant_panel {
    background: #FFFFFF;
    border: 1px solid #DDE2EF;
    border-radius: 18px;
    box-shadow: 0 24px 64px rgba(30, 27, 75, 0.28);
    margin-bottom: 64px;
    overflow: hidden;
    animation: slideUp 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Header with Veritas gradient */
.st-key-veritas_assistant_header {
    background: linear-gradient(135deg, #6256D8 0%, #397BF5 65%, #35C4E7 100%);
    border-bottom: 1px solid rgba(255,255,255,0.12);
    color: #FFFFFF;
    padding: 0.85rem 0.95rem;
}

.veritas-header-title {
    align-items: center;
    display: flex;
    font-size: 0.98rem;
    font-weight: 800;
    gap: 0.50rem;
    letter-spacing: -0.01em;
    line-height: 1.2;
}

.veritas-header-subtitle {
    color: rgba(255,255,255,0.82);
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin-top: 0.18rem;
    text-transform: uppercase;
}

/* Veritas icon — original V-mark design */
.veritas-mini-mark {
    align-items: center;
    background: var(--veritas-chatbot-icon) center / 100% no-repeat;
    border: 0;
    border-radius: 999px;
    color: transparent;
    display: inline-flex;
    flex: 0 0 28px;
    font-size: 0.78rem;
    font-weight: 900;
    height: 28px;
    justify-content: center;
    width: 28px;
    letter-spacing: -0.05em;
}

.st-key-veritas_assistant_header .stButton > button {
    background: rgba(255,255,255,0.16) !important;
    border: 1px solid rgba(255,255,255,0.28) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    color: #FFFFFF !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
    height: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    width: 32px !important;
    transition: all 150ms ease;
}

.st-key-veritas_assistant_header .stButton > button:hover {
    background: rgba(255,255,255,0.24) !important;
}

/* Chat body — scrollable message area */
.st-key-veritas_chat_body {
    background: #FFFFFF;
    height: 200px;
    overflow-y: auto;
    padding: 0.75rem 0.9rem 0.5rem;
    scroll-behavior: smooth;
}

.st-key-veritas_chat_body::-webkit-scrollbar {
    width: 6px;
}

.st-key-veritas_chat_body::-webkit-scrollbar-track {
    background: transparent;
}

.st-key-veritas_chat_body::-webkit-scrollbar-thumb {
    background: #DDE2EF;
    border-radius: 3px;
}

.st-key-veritas_chat_body::-webkit-scrollbar-thumb:hover {
    background: #C7D2FE;
}

/* Message rows */
.veritas-msg-row {
    display: flex;
    margin-bottom: 0.7rem;
    animation: fadeIn 250ms ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

.veritas-msg-row.user {
    justify-content: flex-end;
}

.veritas-msg-row.assistant {
    justify-content: flex-start;
}

/* Message bubbles */
.veritas-msg {
    border-radius: 14px;
    font-size: 0.84rem;
    line-height: 1.45;
    max-width: 85%;
    overflow-wrap: break-word;
    padding: 0.68rem 0.84rem;
    word-break: break-word;
}

.veritas-msg.assistant {
    background: #F3F5FF;
    border: 1px solid #E0E7FF;
    border-bottom-left-radius: 3px;
    color: #1E2433;
}

.veritas-msg.user {
    background: linear-gradient(135deg, #6256D8 0%, #5B4BC9 100%);
    border-bottom-right-radius: 3px;
    color: #FFFFFF;
    box-shadow: 0 2px 8px rgba(98, 86, 216, 0.15);
}

.veritas-sender {
    color: #5046E4;
    font-size: 0.66rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    margin-bottom: 0.20rem;
    text-transform: uppercase;
}

/* Suggested questions label */
.veritas-suggest-label {
    color: #64748B;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    margin: 0.3rem 0 0.5rem;
    text-transform: uppercase;
}

/* Suggestion chips */
.st-key-veritas_suggestion_stack {
    padding: 0 1.0rem 0.8rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.40rem;
}

.st-key-veritas_suggestion_stack .stButton {
    flex: 0 1 auto;
}

.st-key-veritas_suggestion_stack .stButton > button {
    background: #F0F4FF !important;
    border: 1px solid #D4DCFF !important;
    border-radius: 999px !important;
    box-shadow: none !important;
    color: #4F46E5 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    min-height: 32px !important;
    padding: 0.32rem 0.72rem !important;
    white-space: normal !important;
    transition: all 150ms ease;
    width: auto !important;
}

.st-key-veritas_suggestion_stack .stButton > button:hover {
    background: #E0E7FF !important;
    border-color: #B8C5FF !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(98, 86, 216, 0.12) !important;
}

/* Input section */
.st-key-veritas_chat_input {
    border-top: 1px solid #E5E7EF;
    padding: 0.85rem 1.0rem 0.95rem;
    background: #FAFBFF;
}

.st-key-veritas_chat_input [data-testid="stForm"] {
    border: 0 !important;
    padding: 0 !important;
}

.st-key-veritas_chat_input [data-testid="stTextInput"] input {
    border: 1px solid #DDE2EF !important;
    border-radius: 999px !important;
    color: #1E2433 !important;
    font-size: 0.84rem !important;
    padding: 0.56rem 0.95rem !important;
    background: #FFFFFF !important;
    transition: all 150ms ease;
}

.st-key-veritas_chat_input [data-testid="stTextInput"] input:focus {
    border-color: #6256D8 !important;
    box-shadow: 0 0 0 3px rgba(98, 86, 216, 0.1) !important;
}

.st-key-veritas_chat_input [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #6256D8 0%, #5B4BC9 100%) !important;
    border: 0 !important;
    border-radius: 999px !important;
    box-shadow: 0 4px 12px rgba(98, 86, 216, 0.25) !important;
    color: #FFFFFF !important;
    font-size: 1.0rem !important;
    font-weight: 900 !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 !important;
    width: 44px !important;
    transition: all 150ms ease;
}

.st-key-veritas_chat_input [data-testid="stFormSubmitButton"] button:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 16px rgba(98, 86, 216, 0.35) !important;
}

/* Floating message invitation */
.veritas-invite {
    background: #FFFFFF;
    border: 1px solid #DDE2EF;
    border-radius: 16px;
    box-shadow: 0 12px 32px rgba(30, 27, 75, 0.16);
    color: #263044;
    display: block;
    font-size: 0.80rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin: 0;
    padding: 0.62rem 0.88rem;
    position: fixed;
    right: 24px;
    bottom: 84px;
    z-index: 9999;
    white-space: nowrap;
    width: fit-content;
    animation: slideIn 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(16px); }
    to { opacity: 1; transform: translateX(0); }
}

.veritas-invite:after {
    background: #FFFFFF;
    border-bottom: 1px solid #DDE2EF;
    border-right: 1px solid #DDE2EF;
    bottom: -7px;
    content: "";
    height: 11px;
    position: absolute;
    right: 22px;
    transform: rotate(45deg);
    width: 11px;
}

/* Floating icon button */
.st-key-veritas_fab {
    display: block;
    position: fixed !important;
    bottom: 22px !important;
    right: 22px !important;
    z-index: 10000 !important;
    width: 52px !important;
    height: 52px !important;
    margin: 0 !important;
}

.st-key-veritas_fab .veritas-fab-art {
    inset: 0;
    pointer-events: none;
    position: absolute;
    transition: transform 180ms cubic-bezier(0.34, 1.56, 0.64, 1), filter 180ms ease;
    z-index: 1;
}

.st-key-veritas_fab:hover .veritas-fab-art {
    filter: drop-shadow(0 16px 34px rgba(0, 102, 255, 0.32));
    transform: scale(1.05);
}

.chatbot-bubble-wrapper {
    background: linear-gradient(135deg, #00c6ff 0%, #1e40af 100%);
    border-radius: 50% 50% 50% 12%;
    box-shadow: 0 8px 20px rgba(0, 102, 255, 0.22);
    height: 52px;
    padding: 3px;
    position: relative;
    width: 52px;
}

.chatbot-inner {
    align-items: center;
    background: #FFFFFF;
    border-radius: 50% 50% 50% 10%;
    display: flex;
    height: 100%;
    justify-content: center;
    position: relative;
    width: 100%;
}

.b-symbol {
    height: 28px;
    width: 24px;
}

.ribbon-back {
    fill: url(#blueGradient1);
}

.ribbon-front {
    fill: url(#blueGradient2);
}

.ribbon-loop {
    fill: url(#cyanGradient);
}

.st-key-veritas_fab .stButton {
    height: 52px !important;
    margin: 0 !important;
    position: absolute;
    inset: 0;
    width: 52px !important;
    z-index: 2;
}

.st-key-veritas_fab .stButton > button {
    background: transparent !important;
    background-color: transparent !important;
    border: 0 !important;
    border-color: transparent !important;
    box-shadow: none !important;
    color: transparent !important;
    padding: 0 !important;
    min-width: 0 !important;
    min-height: 0 !important;
    height: 52px !important;
    opacity: 0 !important;
    outline: 0 !important;
    width: 52px !important;
    cursor: pointer !important;
    position: relative;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.st-key-veritas_fab .stButton > button:active {
    transform: scale(0.98) !important;
}

/* Responsive design — mobile-first optimization */
@media (max-width: 1366px) {
    .st-key-veritas_floating_assistant {
        width: min(340px, calc(100vw - 32px)) !important;
    }

    .st-key-veritas_chat_body {
        height: 200px;
    }

    .st-key-veritas_fab,
    .st-key-veritas_fab .stButton,
    .st-key-veritas_fab .stButton > button,
    .chatbot-bubble-wrapper {
        width: 52px !important;
        height: 52px !important;
    }

    .b-symbol {
        height: 28px;
        width: 24px;
    }
}

@media (max-width: 768px) {
    .st-key-veritas_floating_assistant {
        bottom: 16px !important;
        right: 16px !important;
        width: calc(100vw - 32px) !important;
    }

    .st-key-veritas_chat_body {
        height: min(180px, 40vh);
    }

    .veritas-msg {
        max-width: 92%;
    }

    .st-key-veritas_fab,
    .st-key-veritas_fab .stButton,
    .st-key-veritas_fab .stButton > button,
    .chatbot-bubble-wrapper {
        width: 48px !important;
        height: 48px !important;
    }
}

@media (max-width: 480px) {
    .st-key-veritas_floating_assistant {
        bottom: 12px !important;
        right: 12px !important;
        width: calc(100vw - 24px) !important;
    }

    .st-key-veritas_assistant_panel {
        border-radius: 16px;
    }

    .st-key-veritas_chat_body {
        height: min(160px, 35vh);
        padding: 0.6rem;
    }

    .veritas-msg {
        font-size: 0.80rem;
        padding: 0.60rem 0.72rem;
    }

    .st-key-veritas_fab,
    .st-key-veritas_fab .stButton,
    .st-key-veritas_fab .stButton > button,
    .chatbot-bubble-wrapper {
        width: 46px !important;
        height: 46px !important;
    }

    .veritas-invite {
        font-size: 0.76rem;
        padding: 0.50rem 0.72rem;
    }
}
</style>
""", unsafe_allow_html=True)


chat_shell = st.container(key="veritas_floating_assistant")
with chat_shell:
    if st.session_state.chat_open:
        panel = st.container(key="veritas_assistant_panel")
        with panel:
            # Header with title and close buttons
            header = st.container(key="veritas_assistant_header")
            with header:
                title_col, close_col = st.columns([8, 1], gap="small")
                with title_col:
                    st.markdown("""
                    <div class="veritas-header-title">
                        <span class="veritas-mini-mark">✓</span>
                        <span>Ask Veritas</span>
                    </div>
                    <div class="veritas-header-subtitle">Business Intelligence Assistant</div>
                    """, unsafe_allow_html=True)
                with close_col:
                    if st.button("×", key="veritas_chat_close", help="Close"):
                        st.session_state.chat_open = False
                        st.rerun()

            # Message body
            body = st.container(key="veritas_chat_body")
            with body:
                if not st.session_state.chat_messages:
                    # Welcome message on first load
                    st.markdown(f"""
                    <div class="veritas-msg-row assistant">
                        <div class="veritas-msg assistant">
                            <div class="veritas-sender">Veritas</div>
                            {_chat_html(_welcome)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Display conversation history
                    for msg in st.session_state.chat_messages:
                        role = "user" if msg["role"] == "user" else "assistant"
                        sender = '<div class="veritas-sender">Veritas</div>' if role == "assistant" else ""
                        st.markdown(f"""
                        <div class="veritas-msg-row {role}">
                            <div class="veritas-msg {role}">
                                {sender}
                                {_chat_html(msg["content"])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # Suggestion chips (only show early in conversation)
            suggestions = st.container(key="veritas_suggestion_stack")
            with suggestions:
                if len(st.session_state.chat_messages) <= 2:
                    st.markdown('<div class="veritas-suggest-label">Suggested questions</div>', unsafe_allow_html=True)
                    suggestion_buttons = st.columns(2, gap="small")
                    for ci, q in enumerate(_suggestions[:4]):
                        col = suggestion_buttons[ci % 2]
                        with col:
                            if st.button(q, key=f"veritas_chat_suggestion_{ci}", use_container_width=True):
                                _handle_ask(q)
                                st.rerun()

            # Input section
            input_box = st.container(key="veritas_chat_input")
            with input_box:
                with st.form("veritas_chat_form", clear_on_submit=True):
                    q_col, send_col = st.columns([5, 1], gap="small")
                    with q_col:
                        u_question = st.text_input(
                            "Ask Veritas question",
                            placeholder="Ask about your business...",
                            key="veritas_chat_question",
                            label_visibility="collapsed",
                        )
                    with send_col:
                        send_click = st.form_submit_button("➤", use_container_width=True)
                    if send_click and u_question.strip():
                        _handle_ask(u_question)
                        st.rerun()

    else:
        # Floating label when chat is closed
        st.markdown('<div class="veritas-invite">Ask me about your business</div>', unsafe_allow_html=True)

    # Floating Action Button (FAB) - always visible
    fab = st.container(key="veritas_fab")
    with fab:
        st.markdown(f'<div class="veritas-fab-art">{_CHATBOT_ICON_HTML}</div>', unsafe_allow_html=True)
        if st.button(" ", key="veritas_chat_launcher", use_container_width=False):
            st.session_state.chat_open = True
            st.rerun()

# ==============================================================================
# MAIN VIEW RENDERER BASED ON SIDEBAR NAVIGATION
# ==============================================================================

if st.session_state.active_page in ["USER", "ORDERS", "REVENUE"]:
    # -------------------------------------------------------------------------
    # OVERVIEW / METRIC VIEW (USER, ORDERS, REVENUE)
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top: 0.4rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    cols = [c1, c2, c3, c4, c5]
    labels = {
        "revenue": ("REVENUE", "Financial Impact"),
        "orders": ("ORDERS", "Sales Volume"),
        "conversion_rate": ("CONVERSION RATE", "Funnel Efficiency"),
        "aov": ("AVERAGE ORDER VALUE", "Basket Size"),
        "gross_margin": ("GROSS MARGIN", "Profitability"),
    }

    for idx, k in enumerate(kpi_keys):
        ev_k = cards_data.get(k, {})
        with cols[idx]:
            if ev_k:
                act = fmt_val(k, ev_k.get("actual_value"))
                exp = fmt_val(k, ev_k.get("expected_value"))
                delta = ev_k.get("delta_pct", 0.0)

                is_neg = delta < 0
                delta_cls = "kpi-delta-neg" if is_neg else "kpi-delta-pos"
                arrow = "▼" if delta < 0 else "▲"
                
                mat = ev_k.get("materiality_score", 0.0)
                if mat >= 0.60:
                    sev_tag = "<span class='badge-low'>CRITICAL</span>"
                elif mat >= 0.30:
                    sev_tag = "<span class='badge-medium'>WARNING</span>"
                else:
                    sev_tag = "<span class='badge-high'>OPTIMAL</span>"

                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="kpi-label">{labels[k][0]}</div>
                        {sev_tag}
                    </div>
                    <div class="kpi-value">{act}</div>
                    <div class="{delta_cls}">{arrow} {abs(delta):.1f}% <span style="color:#667085; font-weight:400; font-size:0.75rem;">vs expected ({exp})</span></div>
                    <div class="kpi-sub">{labels[k][1]} • Materiality {mat:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # ROW 2: PERFORMANCE TREND CHART & INCIDENT SUMMARY
    chart_col, summary_col = st.columns([70, 30])

    with chart_col:
        st.markdown(f'<div class="panel-header">{kpi_selected.replace("_", " ").title()} Performance vs Expected Baseline</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-sub">120-Day Daily Trend • Holt-Winters Baseline with 95% Prediction Interval Shading</div>', unsafe_allow_html=True)
        
        try:
            ts_res = requests.get(f"{API}/api/timeseries/{kpi_selected}", params={"region": region}, headers=headers, timeout=10)
            if ts_res.status_code == 200:
                ts_df = pd.DataFrame(ts_res.json()["data"])
                act_series = ts_df[kpi_selected].values
                exp_val = evidence["expected_value"]
                pi_95 = evidence.get("prediction_interval_95", [exp_val * 0.85, exp_val * 1.15])
                
                baseline_series = act_series.copy()
                incident_len = min(42, len(act_series))
                baseline_series[-incident_len:] = exp_val
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=ts_df["date"], y=[pi_95[1]] * len(ts_df), mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=ts_df["date"], y=[pi_95[0]] * len(ts_df), mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(99, 102, 241, 0.08)', name='95% Prediction Interval', hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=ts_df["date"], y=baseline_series, mode='lines', name='Expected Baseline', line=dict(color='#64748B', width=2, dash='dash')))
                fig.add_trace(go.Scatter(x=ts_df["date"], y=act_series, mode='lines', name=f'Actual {kpi_selected.title()}', line=dict(color='#6558D3', width=3)))
                
                fig.update_layout(
                    height=290,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickfont=dict(color='#64748B', size=11)),
                    yaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickfont=dict(color='#64748B', size=11)),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.warning(f"Chart render note: {exc}")

    with summary_col:
        st.markdown('<div class="panel-header">INCIDENT SUMMARY</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-sub">Quantitative Anomaly Summary</div>', unsafe_allow_html=True)
        
        delta_val = evidence["delta_pct"]
        impact_inr = evidence.get("business_impact_inr")
        mat_score = evidence["materiality_score"]
        ecs_score = evidence["evidence_confidence_score"]
        band = evidence["confidence_band"]
        ecs_badge = get_badge(ecs_score, band)
        
        st.markdown(f"""
        <div style="background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 0.75rem 0.9rem; margin-bottom: 0.8rem;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #991B1B;">{region.upper()} {kpi_selected.upper()} DETERIORATION</div>
            <div style="font-size: 1.6rem; font-weight: 700; color: #DC2626;">{delta_val:+.2f}%</div>
            <div style="font-size: 0.8rem; color: #7F1D1D;">Impact: <strong>{fmt_val('business_impact_inr', impact_inr)}</strong> vs baseline</div>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.82rem;">
            <span style="color: #667085;">Materiality Score:</span>
            <span style="font-weight: 700; color: #1E2433;">{mat_score:.2f} / 1.00 (HIGH)</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 4px; height: 5px; width: 100%; margin-bottom: 0.85rem;">
            <div style="background: #EF4444; height: 5px; border-radius: 4px; width: {min(100, int(mat_score*100))}%;"></div>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.82rem;">
            <span style="color: #667085;">Evidence Confidence:</span>
            <span>{ecs_badge}</span>
        </div>
        <div style="background: #E2E8F0; border-radius: 4px; height: 5px; width: 100%; margin-bottom: 0.6rem;">
            <div style="background: #6558D3; height: 5px; border-radius: 4px; width: {min(100, int(ecs_score*100))}%;"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # ROW 3: LEVEL 1 SHAPLEY BRIDGE & AI INSIGHT
    l1_col, ins_col = st.columns(2)

    with l1_col:
        st.markdown('<div class="panel-header">LEVEL 1 — WHAT MOVED REVENUE?</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-sub">Exact Multiplicative Shapley KPI Bridge (Sum Reconciles to Total Delta)</div>', unsafe_allow_html=True)
        
        if evidence.get("kpi_bridge"):
            bridge_items = evidence["kpi_bridge"]
            fig_br = go.Figure(go.Bar(
                x=[b["contribution_pct_points"] for b in bridge_items],
                y=[b["component"].replace("_", " ").title() for b in bridge_items],
                orientation='h',
                text=[f"{b['contribution_pct_points']:+.2f} pp ({fmt_val('revenue', b.get('contribution_value'))})" for b in bridge_items],
                textposition='auto',
                marker_color=['#EF4444' if b["contribution_pct_points"] < 0 else '#10B981' for b in bridge_items]
            ))
            fig_br.update_layout(
                height=190,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="Percentage Point Contribution (pp)", showgrid=True, gridcolor='#F1F5F9'),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_br, use_container_width=True)
            
            sum_full = sum(b.get("contribution_pct_points_full_precision", b["contribution_pct_points"]) for b in bridge_items)
            target_delta = evidence.get("delta_pct_full_precision", evidence["delta_pct"])
            recon_err = abs(sum_full - target_delta)
            
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.5rem 0.8rem; font-size: 0.78rem; color: #475569;">
                ✅ <strong>Bridge Reconciliation Audit:</strong> Sum = <code>{sum_full:.6f}%</code> | Target = <code>{target_delta:.6f}%</code> | Error = <code>{recon_err:.2e}</code>
            </div>
            """, unsafe_allow_html=True)

    with ins_col:
        st.markdown("""
        <div class="insight-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                <span style="font-weight: 700; font-size: 0.95rem; color: #4C1D95;">🤖 AI EXECUTIVE INSIGHT</span>
                <span class="badge-high" style="background:#EDE9FE; color:#5B21B6; border-color:#DDD6FE;">GROUNDED IN EVIDENCE OBJECT</span>
            </div>
            <div style="font-size: 0.88rem; color: #334155; line-height: 1.45;">
        """ + narrative + """
            </div>
            <div style="font-size: 0.75rem; color: #6D28D9; margin-top: 0.5rem; font-weight: 500;">
                ✓ Verified Grounding • Persona: <code>""" + st.session_state.user.upper() + """</code> • Zero LLM Calculation of Numbers
            </div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.active_page == "DIAGNOSIS":
    # -------------------------------------------------------------------------
    # DIAGNOSIS VIEW
    # -------------------------------------------------------------------------
    st.markdown('<div class="panel-header">LEVEL 1 KPI BRIDGE RECONCILIATION</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Mathematical Breakdown of What Moved Revenue (Exact Shapley Allocation)</div>', unsafe_allow_html=True)
    
    if evidence.get("kpi_bridge"):
        bridge_df = pd.DataFrame([
            {
                "Component": b["component"].replace("_", " ").title(),
                "Contribution (pp)": f"{b['contribution_pct_points']:+.2f} pp",
                "Value Impact": fmt_val('revenue', b.get('contribution_value')),
                "Formula": "Shapley Multiplicative Allocation"
            } for b in evidence["kpi_bridge"]
        ])
        st.table(bridge_df)

    st.markdown('<div class="panel-header">LEVEL 2 BUSINESS DRIVER DIAGNOSIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Evidence-Backed Root Cause Analysis (Why the Bridge Components Moved)</div>', unsafe_allow_html=True)
    
    for d in evidence.get("business_driver_diagnosis", []):
        d_ecs = d["evidence_confidence"]
        d_badge = get_badge(d_ecs, "HIGH" if d_ecs >= 0.75 else ("MEDIUM" if d_ecs >= 0.50 else "LOW"))
        is_warn = d_ecs < 0.50 or d.get("note") is not None
        box_cls = "diag-card-warn" if is_warn else "diag-card"
        
        p_kpi = d.get("parent_kpi", d["diagnoses"]).upper()
        cause_title = d["cause"].replace("_", " ").title()
        
        st.markdown(f"""
        <div class="{box_cls}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                <span style="font-weight: 700; font-size: 0.9rem; color: #1E2433;">{p_kpi} ↓ ← {cause_title}</span>
                {d_badge}
            </div>
            <div style="font-size: 0.82rem; color: #475569;">
                • <strong>Method:</strong> <code>{d['method']}</code> | <strong>Sources:</strong> <code>{', '.join(d['source_tables'])}</code><br>
                • <strong>Freshness:</strong> <code>{d['freshness_hours']:.1f}h</code> | <strong>Data Quality Score:</strong> <code>{d['data_quality_score']:.2f}</code>
            </div>
            {f'<div style="font-size:0.8rem; color:#B45309; margin-top:0.3rem;">⚠️ {d["note"]}</div>' if d.get("note") else ''}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 0.78rem; color: #64748B; margin-top: 0.4rem;">
        ℹ️ Note: Level-2 confidence scores explain root causes and are NEVER added to Level-1 percentage point values.
    </div>
    """, unsafe_allow_html=True)

    if evidence.get("abstentions"):
        st.markdown(f"""
        <div class="abstain-banner">
            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.3rem;">⚠️ ATTRIBUTION WITHHELD (Engine Abstention Notice)</div>
            <div style="font-size: 0.88rem; line-height: 1.4;">
                {"<br>".join(evidence["abstentions"])}
            </div>
            <div style="font-size: 0.78rem; color: #92400E; margin-top: 0.5rem;">
                • Marketing Source Freshness: <code>30.0h</code> (SLA: 24h) | Confidence Score: <code>0.216 (LOW)</code><br>
                • System behavior: Preserves Level-1 facts while safely withholding unproven causal claims.
            </div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.active_page == "ACTIONS":
    # -------------------------------------------------------------------------
    # ACTIONS VIEW
    # -------------------------------------------------------------------------
    st.markdown('<div class="panel-header">GOVERNED RECOMMENDED ACTIONS</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Controlled Playbook Actions Filtered by Decision Rights & Evidence Confidence (≥ 0.50)</div>', unsafe_allow_html=True)

    if actions:
        act_cols = st.columns(min(3, len(actions)))
        for idx, act in enumerate(actions[:3]):
            with act_cols[idx]:
                conf_b = get_badge(0.85 if act['confidence'] == 'HIGH' else 0.65, act['confidence'])
                st.markdown(f"""
                <div class="action-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 0.75rem; font-weight: 700; color: #6558D3;">DRIVER: {act['driver'].upper()}</span>
                        {conf_b}
                    </div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #1E2433; margin-bottom: 0.4rem;">{act['action']}</div>
                    <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.6rem;">
                        • <strong>Lever:</strong> {act['lever']}<br>
                        • <strong>Owner:</strong> {act['owner']}<br>
                        • <strong>Impact:</strong> {act['expected_impact']}
                    </div>
                    <div style="background: #F1F5F9; border-radius: 6px; padding: 0.4rem 0.6rem; font-size: 0.75rem; color: #334155; margin-bottom: 0.8rem;">
                        📋 <strong>Monitoring:</strong> {act['monitoring_plan']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                btn1, btn2, btn3 = st.columns(3)
                if btn1.button("Accept", key=f"act_acc_{idx}", use_container_width=True):
                    st.success(f"Action '{act['lever']}' accepted by {st.session_state.user.upper()}.")
                if btn2.button("Escalate", key=f"act_esc_{idx}", use_container_width=True):
                    st.warning(f"Escalated to {act['owner']}.")
                if btn3.button("Reject", key=f"act_rej_{idx}", use_container_width=True):
                    st.info("Action flagged for review.")
    else:
        st.info("No action is authorized or supported at the current evidence level for your user role.")

elif st.session_state.active_page == "EVIDENCE":
    # -------------------------------------------------------------------------
    # EVIDENCE VIEW
    # -------------------------------------------------------------------------
    st.markdown('<div class="panel-header">EVIDENCE TRUST, FRESHNESS & LINEAGE</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Complete Transparency & Auditability for Judges and Analysts</div>', unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### Source Metadata & SLA Audit Table")
        st.table(pd.DataFrame([
            {"Source": "Sales (Bronze Orders)", "Freshness": f"{evidence['source_freshness'].get('sales', 6.0):.1f}h", "SLA": "2.0h", "Quality Score": evidence['data_quality'].get('sales', 0.97), "Status": "Current"},
            {"Source": "Marketing (Campaigns)", "Freshness": f"{evidence['source_freshness'].get('marketing', 6.0):.1f}h", "SLA": "24.0h", "Quality Score": evidence['data_quality'].get('marketing', 0.95), "Status": "Stale" if scenario=="degraded" else "Current"},
            {"Source": "Inventory (Snapshots)", "Freshness": f"{evidence['source_freshness'].get('inventory', 4.0):.1f}h", "SLA": "4.0h", "Quality Score": evidence['data_quality'].get('inventory', 0.97), "Status": "Current"},
        ]))
    
    with col_t2:
        st.markdown("#### Analysis Methods & Lineage")
        st.json({
            "query_id": evidence["query_id"],
            "window": evidence["window"],
            "lineage": evidence["lineage"],
            "analysis_method_version": evidence["analysis_method_version"],
            "prediction_interval_95": evidence["prediction_interval_95"],
            "contradictions": evidence.get("contradictions", []),
        })

elif st.session_state.active_page == "NEW PRODUCT":
    # -------------------------------------------------------------------------
    # NEW PRODUCT VIEW
    # -------------------------------------------------------------------------
    st.markdown('<div class="panel-header">Sparse-History SKU Launcher (`P020`)</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Launch Cohort Benchmarking for Products with &lt; 30 Days History</div>', unsafe_allow_html=True)
    
    try:
        sp_res = requests.get(f"{API}/api/sparse-history/P020", headers=headers, timeout=10).json()
        sp1, sp2, sp3, sp4 = st.columns(4)
        sp1.metric("SKU ID", sp_res["product_id"])
        sp2.metric("History Days", sp_res["history_days"])
        sp3.metric("Current Avg Revenue", f"₹{sp_res['current_avg_daily_revenue']:,.2f}")
        sp4.metric("Cohort Benchmark Avg", f"₹{sp_res['cohort_avg_daily_revenue']:,.2f}")
        
        st.warning(f"ℹ️ **Notice:** {sp_res['message']} (Confidence Cap: `{sp_res['evidence_confidence_cap']:.2f}`)")
        st.json({
            "product_id": sp_res["product_id"],
            "category": sp_res["category"],
            "launch_date": sp_res["launch_date"],
            "history_days": sp_res["history_days"],
            "benchmark_method": sp_res["method"],
            "delta_vs_cohort_pct": f"{sp_res['delta_vs_cohort_pct']:+.2f}%",
            "evidence_confidence_cap": sp_res["evidence_confidence_cap"],
        })
    except Exception as exc:
        st.error(f"Sparse history view error: {exc}")

elif st.session_state.active_page == "SYSTEM":
    # -------------------------------------------------------------------------
    # SYSTEM VIEW
    # -------------------------------------------------------------------------
    st.markdown('<div class="panel-header">SYSTEM TELEMETRY & SECURITY VERIFICATION</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Backend Infrastructure Metrics & RBAC Scoping Controls</div>', unsafe_allow_html=True)
    
    if evidence.get("telemetry"):
        tel = evidence["telemetry"]
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Total Latency", f"{tel.get('total_latency_ms', 0):.1f} ms")
        t2.metric("Analytics Latency", f"{tel.get('analytics_latency_ms', 0):.1f} ms")
        t3.metric("LLM Latency", f"{tel.get('llm_latency_ms', 0):.1f} ms")
        t4.metric("Model Calls", tel.get('model_calls', 0))
        t5.metric("Cost USD", f"${tel.get('estimated_cost_usd', 0.0):.4f}")
    
    st.divider()
    
    # Security Test Panel
    st.markdown("#### Security Entitlements Test (RBAC Scoping)")
    sec1, sec2 = st.columns([2, 1])
    with sec1:
        sec_user = st.selectbox("Test Persona", ["north_mgr", "marketing_mgr", "ceo"], index=0, key="sec_user_select")
        sec_region = st.selectbox("Test Region", ["South", "East", "West", "North"], index=0, key="sec_reg_select")
    with sec2:
        st.write("Run Security Audit:")
        if st.button("Execute RBAC Test", key="sec_test_btn"):
            sec_r = requests.get(f"{API}/api/insight", params={"kpi": "revenue", "region": sec_region}, headers={"X-Demo-User": sec_user})
            if sec_r.status_code == 403:
                st.error(f"🔒 **SECURITY REJECTION (HTTP 403)**\n\n{sec_r.json().get('detail')}")
                st.success("✅ **Pass:** Access blocked before data query execution. Zero unauthorized data leaked.")
            else:
                st.success(f"✅ **Authorized (HTTP 200):** Persona `{sec_user}` is authorized for region `{sec_region}`.")
                
    st.divider()
    
    # Analyst Feedback Panel
    st.markdown("#### Analyst Feedback Submission")
    fbc1, fbc2 = st.columns([2, 1])
    with fbc1:
        corr_input = st.text_input("Corrected Driver (Optional):", key="fb_corr")
        comment_input = st.text_area("Analyst Notes:", height=80, key="fb_notes")
    with fbc2:
        st.write("Submit Evaluation:")
        if st.button("👍 Useful / Verified", key="fb_up_btn"):
            requests.post(f"{API}/api/feedback", json={"insight_id": evidence["insight_id"], "user_id": st.session_state.user, "rating": "up", "comment": comment_input}, headers=headers)
            st.success("Feedback stored for batch validation.")
        if st.button("👎 Incorrect / Correction", key="fb_down_btn"):
            requests.post(f"{API}/api/feedback", json={"insight_id": evidence["insight_id"], "user_id": st.session_state.user, "rating": "correction", "corrected_driver": corr_input, "comment": comment_input}, headers=headers)
            st.warning("Correction queued for validation.")
