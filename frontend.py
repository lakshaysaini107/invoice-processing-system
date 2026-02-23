import io
import json
import mimetypes
import subprocess
import sys
import time
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException
import streamlit as st


def apply_futuristic_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        :root {
            --bg-0: #f6fbff;
            --bg-1: #edf7ff;
            --bg-2: #dbf3ff;
            --panel: rgba(255, 255, 255, 0.82);
            --panel-soft: #f8fbff;
            --line: #d5e6f5;
            --line-strong: #9cc3e8;
            --text-main: #16304a;
            --text-dim: #5f7894;
            --accent-a: #0ea5e9;
            --accent-b: #2563eb;
            --accent-c: #0284c7;
            --good: #15803d;
            --warn: #b45309;
            --card-shadow: 0 10px 36px rgba(20, 55, 91, 0.10);
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(1000px 340px at 8% -8%, rgba(14, 165, 233, 0.18), transparent 58%),
                radial-gradient(720px 300px at 90% 1%, rgba(37, 99, 235, 0.15), transparent 62%),
                linear-gradient(170deg, var(--bg-0), var(--bg-1) 56%, var(--bg-2));
            color: var(--text-main);
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.76);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--line);
        }

        [data-testid="stSidebar"] {
            display: none !important;
        }

        [data-testid="collapsedControl"] {
            display: none !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #f4faff 0%, #edf6ff 100%);
            border-right: 1px solid var(--line);
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            font-family: "Outfit", sans-serif !important;
            letter-spacing: 0.01em !important;
            color: #112741 !important;
            margin-bottom: 0.45rem !important;
        }

        p, label, span, div, input, textarea {
            font-family: "Plus Jakarta Sans", sans-serif !important;
            color: var(--text-main);
        }

        [data-testid="stCaptionContainer"] p {
            color: var(--text-dim) !important;
        }

        [data-testid="stSidebar"] * {
            color: #20344d !important;
        }

        [data-testid="stSidebar"] [data-testid="stTextInput"] input {
            background: #ffffff !important;
            border: 1px solid var(--line) !important;
            color: var(--text-main) !important;
        }

        [data-testid="stSidebar"] [data-testid="stButton"] > button {
            color: #ffffff !important;
        }

        .space-brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin-bottom: 0.8rem;
            padding: 0.68rem 0.72rem;
            border-radius: 14px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.88);
            box-shadow: 0 8px 22px rgba(22, 56, 91, 0.09);
        }

        .space-logo {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(145deg, #e0f3ff, #f0f8ff);
            border: 1px solid var(--line-strong);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .space-brand-title {
            font-family: "Outfit", sans-serif !important;
            font-size: 0.96rem;
            color: #153450 !important;
            line-height: 1.2;
            font-weight: 700;
        }

        .space-brand-sub {
            color: var(--text-dim) !important;
            font-size: 0.8rem;
            margin-top: 0.1rem;
        }

        .hero-title-wrap {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.16rem;
            animation: rise-fade 0.55s ease-out both;
        }

        .hero-logo {
            width: 46px;
            height: 46px;
            border-radius: 13px;
            background: linear-gradient(145deg, #ddf1ff, #f3fbff);
            border: 1px solid var(--line-strong);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            box-shadow: 0 8px 18px rgba(15, 65, 108, 0.1);
        }

        .hero-title-text {
            font-family: "Outfit", sans-serif !important;
            color: #0f2b45 !important;
            font-weight: 800;
            font-size: clamp(1.75rem, 3vw, 2.35rem);
            letter-spacing: 0.012em;
            line-height: 1.06;
            margin: 0;
        }

        .hero-subtitle {
            margin-top: 0.2rem;
            color: var(--text-dim) !important;
            font-size: 0.98rem;
            max-width: 900px;
            animation: rise-fade 0.72s ease-out both;
        }

        .hero-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.68rem 0 0.3rem 0;
            animation: rise-fade 0.9s ease-out both;
        }

        .hero-chip {
            border: 1px solid #c7ddf3;
            border-radius: 999px;
            padding: 0.24rem 0.62rem;
            font-size: 0.74rem;
            color: #1a4368 !important;
            background: rgba(255, 255, 255, 0.78);
        }

        .section-head {
            margin: 0.2rem 0 0.8rem 0;
            padding: 0.72rem 0.82rem;
            border-radius: 12px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.72);
            box-shadow: 0 6px 22px rgba(18, 59, 97, 0.08);
            animation: rise-fade 0.45s ease-out both;
        }

        .section-title {
            font-family: "Outfit", sans-serif !important;
            font-weight: 700;
            color: #103252 !important;
            font-size: 1.04rem;
            margin-bottom: 0.1rem;
        }

        .section-sub {
            color: var(--text-dim) !important;
            font-size: 0.88rem;
        }

        .dash-panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 16px;
            margin: 0.5rem 0 1.05rem 0;
            backdrop-filter: blur(6px);
            box-shadow: var(--card-shadow);
        }

        .dash-title {
            font-family: "Outfit", sans-serif !important;
            font-weight: 700;
            color: #11324f !important;
        }

        .dash-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .status-pill {
            border-radius: 999px;
            padding: 4px 11px;
            font-size: 0.7rem;
            font-weight: 700;
            border: 1px solid var(--line);
            color: #1e3149 !important;
            background: var(--panel-soft);
        }

        .dash-panel-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .dash-metric {
            border: 1px solid var(--line);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.86);
            padding: 10px 12px;
        }

        .dash-label {
            color: var(--text-dim) !important;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }

        .dash-value {
            color: #1f2d3d !important;
            font-size: 1.1rem;
            margin-top: 0.18rem;
            font-weight: 800;
        }

        .status-ok {
            color: var(--good) !important;
            background: rgba(22, 163, 74, 0.10);
            border-color: rgba(22, 163, 74, 0.26);
        }

        .status-bad {
            color: var(--warn) !important;
            background: rgba(217, 119, 6, 0.10);
            border-color: rgba(217, 119, 6, 0.26);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid var(--line);
            padding-bottom: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--line);
            border-radius: 10px;
            color: var(--text-dim) !important;
            padding: 8px 14px;
            transition: all 0.2s ease;
        }

        .stTabs [aria-selected="true"] {
            color: #0f416f !important;
            border: 1px solid var(--line-strong);
            background: #ecf6ff;
            box-shadow: 0 4px 12px rgba(11, 73, 130, 0.12);
        }

        .stButton > button {
            border: 1px solid var(--accent-c);
            border-radius: 10px;
            background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
            color: #ffffff;
            font-weight: 700;
            letter-spacing: 0.01em;
            box-shadow: 0 6px 16px rgba(18, 100, 186, 0.25);
            transition: filter 0.15s ease, transform 0.15s ease;
        }

        .stButton > button:hover {
            filter: brightness(0.97);
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(18, 100, 186, 0.28);
        }

        .stButton > button:focus:not(:active) {
            border-color: var(--accent-c);
            box-shadow: 0 0 0 0.16rem rgba(14, 165, 233, 0.22);
        }

        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid var(--line) !important;
            border-radius: 10px !important;
            color: var(--text-main) !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: #84b8f3 !important;
            box-shadow: 0 0 0 0.14rem rgba(14, 165, 233, 0.15) !important;
        }

        .stCheckbox, .stRadio {
            background: transparent;
        }

        .stMarkdown p, .stMarkdown li, .stMarkdown span {
            color: var(--text-main) !important;
        }

        div[data-testid="stFileUploader"] {
            border: 1px dashed var(--line-strong);
            border-radius: 12px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.58);
        }

        div[data-testid="stAlert"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            background: #ffffff;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.9);
        }

        div[data-testid="stProgressBar"] div[role="progressbar"] {
            background: linear-gradient(90deg, var(--accent-a), var(--accent-b)) !important;
        }

        [data-testid="stMetric"] {
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.35rem 0.65rem;
            background: rgba(255, 255, 255, 0.82);
        }

        code, pre {
            border-radius: 8px !important;
            border: 1px solid var(--line) !important;
            background: #f5f8fd !important;
            color: #1f2d3d !important;
        }

        @keyframes rise-fade {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 900px) {
            .dash-panel-grid {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 1.55rem !important;
            }

            .dash-head {
                flex-direction: column;
                align-items: flex-start;
            }

            .hero-logo {
                width: 40px;
                height: 40px;
            }

            .hero-chip-row {
                margin-top: 0.52rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    st.markdown(
        """
        <div class="space-brand">
          <div class="space-logo">
            <svg width="26" height="26" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <defs>
                <linearGradient id="logo_grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#37ddff"/>
                  <stop offset="100%" stop-color="#4386ff"/>
                </linearGradient>
              </defs>
              <polygon points="50,5 88,28 88,72 50,95 12,72 12,28" fill="none" stroke="url(#logo_grad)" stroke-width="6"/>
              <path d="M50 22 L73 78 L61 78 L56 66 L44 66 L39 78 L27 78 Z" fill="url(#logo_grad)"/>
              <rect x="43" y="50" width="14" height="7" fill="#071a31"/>
            </svg>
          </div>
          <div>
            <div class="space-brand-title">Invoice Intelligence AI</div>
            <div class="space-brand-sub">Invoice Workspace</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_main_header():
    st.markdown(
        """
        <div class="hero-title-wrap">
          <div class="hero-logo">
            <svg width="26" height="26" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <defs>
                <linearGradient id="logo_grad_main" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#37ddff"/>
                  <stop offset="100%" stop-color="#4386ff"/>
                </linearGradient>
              </defs>
              <polygon points="50,5 88,28 88,72 50,95 12,72 12,28" fill="none" stroke="url(#logo_grad_main)" stroke-width="6"/>
              <path d="M50 22 L73 78 L61 78 L56 66 L44 66 L39 78 L27 78 Z" fill="url(#logo_grad_main)"/>
              <rect x="43" y="50" width="14" height="7" fill="#071a31"/>
            </svg>
          </div>
          <div class="hero-title-text">Invoice Processing Dashboard</div>
        </div>
        <div class="hero-subtitle">
          Upload files, trigger OCR extraction, manually review fields, and export structured output from one clean workspace.
        </div>
        <div class="hero-chip-row">
          <span class="hero-chip">Upload</span>
          <span class="hero-chip">Processing</span>
          <span class="hero-chip">Manual Review</span>
          <span class="hero-chip">Export</span>
          <span class="hero-chip">History</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def render_dashboard_panel(backend_ok: bool, backend_status: str):
    backend_class = "status-ok" if backend_ok else "status-bad"
    backend_label = "ONLINE" if backend_ok else "OFFLINE"
    uploaded_count = len(st.session_state.last_uploads)
    history_count = len(st.session_state.history or [])
    started_at = st.session_state.get("backend_started_at")
    uptime = format_duration(time.time() - started_at) if started_at else "n/a"
    panel = f"""
    <div class="dash-panel">
      <div class="dash-head">
        <div class="dash-title">Invoice Overview</div>
        <div class="status-pill {backend_class}">{backend_label}</div>
      </div>
      <div class="dash-panel-grid">
        <div class="dash-metric">
          <div class="dash-label">Backend</div>
          <div class="dash-value">{backend_status}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">Uploaded IDs</div>
          <div class="dash-value">{uploaded_count}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">History Rows</div>
          <div class="dash-value">{history_count}</div>
        </div>
        <div class="dash-metric">
          <div class="dash-label">Backend Uptime</div>
          <div class="dash-value">{uptime}</div>
        </div>
      </div>
      <div class="dash-label" style="margin-top:10px;">Live sync with backend endpoint and session state telemetry.</div>
    </div>
    """
    st.markdown(panel, unsafe_allow_html=True)


def render_section_intro(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="section-head">
          <div class="section-title">{title}</div>
          <div class="section-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def response_payload(res: Any) -> Any:
    if isinstance(res, dict):
        return res
    try:
        return res.json()
    except Exception:
        return {"error": getattr(res, "text", "Unexpected response payload.")}


def ensure_dict_payload(payload: Any) -> Dict[str, Any]:
    return payload if isinstance(payload, dict) else {"raw_response": payload}


def start_processing_for_upload(invoice_id: str, use_cache: bool) -> Dict[str, Any]:
    proc_res = post_json(
        f"{st.session_state.base_url}/process/start",
        {"invoice_id": invoice_id, "use_cache": use_cache},
    )
    if isinstance(proc_res, dict) and proc_res.get("_error"):
        return {"error": proc_res["_error"]}
    payload = ensure_dict_payload(response_payload(proc_res))
    if getattr(proc_res, "status_code", 200) != 200:
        detail = payload.get("detail") or payload.get("error") or str(payload)
        return {"error": detail}
    return payload


def upload_invoice_entries(
    entries: List[Tuple[str, bytes, str]],
    auto_process: bool,
    use_cache: bool,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    total = len(entries)
    progress = st.progress(0.0) if total else None

    for index, (name, content, mime) in enumerate(entries, start=1):
        res = upload_single_file(st.session_state.base_url, name, content, mime)
        if isinstance(res, dict) and res.get("_error"):
            results.append({"file": name, "status": "error", "data": res["_error"], "processing": None})
        else:
            data = response_payload(res)
            invoice_id = data.get("invoice_id") if isinstance(data, dict) else None
            if invoice_id:
                st.session_state.last_uploads.append(invoice_id)
            processing: Optional[Dict[str, Any]] = None
            if auto_process and getattr(res, "status_code", None) == 200 and invoice_id:
                processing = start_processing_for_upload(invoice_id, use_cache)

            results.append(
                {
                    "file": name,
                    "status": getattr(res, "status_code", "error"),
                    "data": data,
                    "processing": processing,
                }
            )

        if progress:
            progress.progress(index / total)

    if progress:
        progress.empty()
    return results


def render_upload_results(results: List[Dict[str, Any]], auto_process: bool):
    if not results:
        st.info("No files were uploaded.")
        return

    uploaded = 0
    failed = 0
    processing_started = 0
    rows = []

    for item in results:
        status = item.get("status")
        uploaded_ok = isinstance(status, int) and 200 <= status < 300
        if uploaded_ok:
            uploaded += 1
        else:
            failed += 1

        data = item.get("data") if isinstance(item.get("data"), dict) else {}
        invoice_id = data.get("invoice_id") if isinstance(data, dict) else "-"

        process_text = "Not requested"
        process_info = item.get("processing")
        if auto_process:
            if isinstance(process_info, dict):
                if process_info.get("error"):
                    process_text = "Failed"
                else:
                    process_text = process_info.get("status") or process_info.get("message") or "Started"
                    processing_started += 1
            else:
                process_text = "Skipped"

        rows.append(
            {
                "File": item.get("file"),
                "Upload": "Success" if uploaded_ok else f"Failed ({status})",
                "Invoice ID": invoice_id,
                "Auto Processing": process_text,
            }
        )

    metric_columns = st.columns(4 if auto_process else 3)
    metric_columns[0].metric("Files", len(results))
    metric_columns[1].metric("Uploaded", uploaded)
    metric_columns[2].metric("Failed", failed)
    if auto_process:
        metric_columns[3].metric("Processing Queued", processing_started)

    st.dataframe(rows, use_container_width=True)
    with st.expander("View full upload responses"):
        st.json(results)


def init_state():
    if "base_url" not in st.session_state:
        st.session_state.base_url = "http://localhost:8000/api"
    if "history" not in st.session_state:
        st.session_state.history = []
    if "review_details" not in st.session_state:
        st.session_state.review_details = None
    if "review_json" not in st.session_state:
        st.session_state.review_json = ""
    if "last_uploads" not in st.session_state:
        st.session_state.last_uploads = []
    if "process_status" not in st.session_state:
        st.session_state.process_status = None
    if "backend_proc" not in st.session_state:
        st.session_state.backend_proc = None
    if "backend_started_at" not in st.session_state:
        st.session_state.backend_started_at = None
    if "backend_autostart_attempted" not in st.session_state:
        st.session_state.backend_autostart_attempted = False


def api_headers() -> dict:
    return {}

def root_url(base_url: str) -> str:
    return base_url[:-4] if base_url.endswith("/api") else base_url

def check_backend(base_url: str, timeout: float = 5.0) -> Tuple[bool, str]:
    try:
        res = requests.get(f"{root_url(base_url)}/health", timeout=timeout)
        if res.status_code == 200:
            return True, "healthy"
        return False, f"status {res.status_code}"
    except RequestException as e:
        return False, str(e)

def start_backend_process() -> Tuple[bool, str]:
    try:
        if st.session_state.backend_proc and st.session_state.backend_proc.poll() is None:
            return True, "Backend process already running."
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
        proc = subprocess.Popen(cmd, cwd=".")
        st.session_state.backend_proc = proc
        st.session_state.backend_started_at = time.time()
        return True, "Backend process started."
    except Exception as e:
        return False, f"Failed to start backend: {e}"

def auto_start_backend():
    if st.session_state.backend_autostart_attempted:
        return
    st.session_state.backend_autostart_attempted = True
    ok, _ = start_backend_process()
    if not ok:
        return
    # Wait briefly for the server to come up
    for _ in range(10):
        time.sleep(0.5)
        ok, status = check_backend(st.session_state.base_url, timeout=2.0)
        if ok:
            st.session_state.backend_ok = True
            st.session_state.backend_status = status
            return


def post_json(url: str, payload: Optional[dict] = None, use_auth: bool = True, timeout: float = 15.0):
    headers = {}
    if use_auth:
        headers.update(api_headers())
    try:
        if payload is None:
            return requests.post(url, headers=headers, timeout=timeout)
        headers["Content-Type"] = "application/json"
        return requests.post(url, json=payload, headers=headers, timeout=timeout)
    except RequestException as e:
        return {"_error": f"Backend offline. Start it on port 8000. Details: {e}"}


def get_json(url: str, timeout: float = 15.0):
    try:
        return requests.get(url, headers=api_headers(), timeout=timeout)
    except RequestException as e:
        return {"_error": f"Backend offline. Start it on port 8000. Details: {e}"}


def upload_single_file(base_url: str, filename: str, content: bytes, content_type: str):
    files = {"files": (filename, content, content_type)}
    try:
        return requests.post(f"{base_url}/invoices/upload", headers=api_headers(), files=files)
    except RequestException as e:
        return {"_error": str(e)}


def build_files_from_zip(zip_bytes: bytes) -> List[Tuple[str, bytes, str]]:
    results = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.split("/")[-1].strip()
            if not name:
                continue
            content = zf.read(info)
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            results.append((name, content, mime))
    return results


def render_upload():
    render_section_intro(
        "Upload Invoices",
        "Add single files or zip folders, then optionally queue processing automatically.",
    )

    selector_col, hint_col = st.columns([2, 1])
    with selector_col:
        mode = st.radio("Upload Mode", ["Batch files", "Folder (zip)"], horizontal=True, key="upload_mode")
    with hint_col:
        st.caption("Supported: PDF, PNG, JPG, JPEG, TIF, TIFF")
        st.caption("Zip mode is useful for full invoice batches.")

    option_col_1, option_col_2 = st.columns(2)
    with option_col_1:
        auto_process = st.checkbox("Auto-start processing after upload", value=True, key="upload_auto_process")
    with option_col_2:
        use_cache = st.checkbox("Use cache for processing", value=True, key="upload_use_cache")

    if mode == "Batch files":
        files = st.file_uploader(
            "Select files",
            type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
            accept_multiple_files=True,
            key="upload_batch_files",
        )
        if st.button("Upload Selected Files", use_container_width=True, type="primary", key="upload_batch_button"):
            if not files:
                st.warning("Please select at least one file.")
                return
            entries = [
                (f.name, f.getvalue(), f.type or "application/octet-stream")
                for f in files
            ]
            results = upload_invoice_entries(entries, auto_process=auto_process, use_cache=use_cache)
            render_upload_results(results, auto_process=auto_process)
    else:
        zip_file = st.file_uploader(
            "Upload a zip file containing invoices",
            type=["zip"],
            key="upload_zip_file",
        )
        if st.button("Upload Zip Contents", use_container_width=True, type="primary", key="upload_zip_button"):
            if not zip_file:
                st.warning("Please select a zip file.")
                return
            try:
                extracted = build_files_from_zip(zip_file.getvalue())
            except Exception as e:
                st.error(f"Failed to read zip: {e}")
                return
            if not extracted:
                st.warning("No files found in zip.")
                return
            results = upload_invoice_entries(extracted, auto_process=auto_process, use_cache=use_cache)
            render_upload_results(results, auto_process=auto_process)


def render_processing():
    render_section_intro(
        "Processing",
        "Start extraction for any invoice and monitor progress in real time.",
    )
    st.caption("Use the invoice ID returned in Upload to start or check processing.")

    invoice_id = st.text_input("Invoice ID", key="process_id", placeholder="Enter invoice ID")
    use_cache = st.checkbox("Use cache when available", value=True, key="process_cache")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Processing", use_container_width=True, type="primary", key="start_processing_btn"):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            payload = {"invoice_id": invoice_id, "use_cache": use_cache}
            res = post_json(f"{st.session_state.base_url}/process/start", payload)
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            data = ensure_dict_payload(response_payload(res))
            if res.status_code == 200:
                st.success(data.get("message", "Processing started"))
                st.session_state.process_status = data
            else:
                st.error(data)
    with col2:
        if st.button("Check Status", use_container_width=True, key="check_processing_btn"):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            res = get_json(f"{st.session_state.base_url}/process/status/{invoice_id}")
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            data = ensure_dict_payload(response_payload(res))
            if res.status_code == 200:
                st.session_state.process_status = data
            else:
                st.error(data)
    with col3:
        if st.button("Clear Status", use_container_width=True, key="clear_processing_btn"):
            st.session_state.process_status = None

    status = st.session_state.process_status
    if not status:
        st.info("No processing status yet. Start processing or check an existing invoice.")
        return

    raw_progress = status.get("progress", 0)
    progress_value = raw_progress if isinstance(raw_progress, (int, float)) else 0
    clamped_progress = max(0.0, min(progress_value / 100, 1.0))
    st.progress(clamped_progress)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Progress", f"{progress_value:.0f}%")
    metric_col2.metric("Status", str(status.get("status", "unknown")).upper())
    metric_col3.metric("Current Step", str(status.get("current_step") or "-"))

    if status.get("error_message"):
        st.error(status.get("error_message"))

    if status.get("extracted_data"):
        with st.expander("View extracted data"):
            st.json(status.get("extracted_data"))


def render_review():
    render_section_intro(
        "Manual Review",
        "Load extracted invoice data, make corrections, and submit approval with notes.",
    )
    invoice_id = st.text_input("Invoice ID", key="review_id", placeholder="Enter invoice ID")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Details", use_container_width=True, type="primary", key="load_review_btn"):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            res = get_json(f"{st.session_state.base_url}/review/{invoice_id}/details")
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            data = response_payload(res)
            if res.status_code == 200:
                if not isinstance(data, dict):
                    st.error("Unexpected review response format.")
                    return
                st.session_state.review_details = data
                st.session_state.review_json = json.dumps(data.get("extracted_data", {}), indent=2)
            else:
                st.error(data)
    with col2:
        if st.button("Clear Review", use_container_width=True, key="clear_review_btn"):
            st.session_state.review_details = None
            st.session_state.review_json = ""

    details = st.session_state.review_details
    if not details:
        st.info("Load invoice details to review extracted data.")
        return

    if not isinstance(details, dict):
        st.error("Unexpected review details format.")
        return

    if details.get("invoice_id") != invoice_id:
        st.info("Loaded details do not match the current invoice ID. Reload details.")
        return

    extracted_data = details.get("extracted_data", {})
    confidence_scores = details.get("confidence_scores", {})
    meta_col1, meta_col2, meta_col3 = st.columns(3)
    meta_col1.metric("Filename", details.get("filename") or "-")
    meta_col2.metric("Processing Status", details.get("processing_status") or "-")
    meta_col3.metric("Extracted Fields", len(extracted_data))

    if confidence_scores:
        confidence_rows = []
        for field, payload in confidence_scores.items():
            confidence = payload.get("confidence") if isinstance(payload, dict) else payload
            if isinstance(confidence, (int, float)):
                if confidence <= 1:
                    confidence_text = f"{confidence * 100:.1f}%"
                else:
                    confidence_text = f"{confidence:.1f}%"
            else:
                confidence_text = str(confidence)
            confidence_rows.append({"Field": field, "Confidence": confidence_text})
        st.dataframe(confidence_rows, use_container_width=True)

    edited_json = st.text_area(
        "Extracted Data (JSON)",
        key="review_json",
        height=320,
        help="Edit values directly in JSON format before submitting.",
    )
    notes = st.text_area("Review Notes", key="review_notes", placeholder="Optional reviewer notes")
    approved = st.checkbox("Approve invoice", value=True, key="review_approved")

    if st.button("Submit Review", use_container_width=True, type="primary", key="submit_review_btn"):
        if not invoice_id:
            st.warning("Please enter an invoice ID.")
            return
        try:
            edited_data = json.loads(edited_json) if edited_json.strip() else {}
        except Exception as e:
            st.error(f"Invalid JSON: {e}")
            return

        corrections = []
        for key in set(extracted_data.keys()) | set(edited_data.keys()):
            original_value = extracted_data.get(key)
            corrected_value = edited_data.get(key)
            if corrected_value != original_value:
                confidence_entry = confidence_scores.get(key, {}) if isinstance(confidence_scores, dict) else {}
                corrections.append(
                    {
                        "field_name": key,
                        "original_value": original_value,
                        "corrected_value": corrected_value,
                        "confidence": confidence_entry.get("confidence") if isinstance(confidence_entry, dict) else None,
                    }
                )

        payload = {
            "invoice_id": invoice_id,
            "corrections": corrections,
            "notes": notes or None,
            "approved": approved,
        }
        res = post_json(f"{st.session_state.base_url}/review/{invoice_id}/submit", payload)
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        data = response_payload(res)
        if res.status_code == 200:
            st.success(f"Review submitted with {len(corrections)} correction(s).")
            with st.expander("View submission response"):
                st.json(data)
        else:
            st.error(data)


def render_export():
    render_section_intro(
        "Export",
        "Generate a downloadable output for a single invoice in JSON, CSV, or Excel format.",
    )
    input_col, format_col = st.columns([2, 1])
    with input_col:
        invoice_id = st.text_input("Invoice ID", key="export_id", placeholder="Enter invoice ID")
    with format_col:
        export_format = st.selectbox(
            "Format",
            ["json", "csv", "excel"],
            key="export_format",
            format_func=lambda value: value.upper(),
        )

    if st.button("Generate Export", use_container_width=True, type="primary", key="export_btn"):
        if not invoice_id:
            st.warning("Please enter an invoice ID.")
            return
        url = f"{st.session_state.base_url}/export/single/{invoice_id}?format={export_format}"
        res = post_json(url)
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        if export_format == "json":
            data = response_payload(res)
            if res.status_code != 200:
                st.error(data)
                return
            payload = data.get("data", data) if isinstance(data, dict) else data
            try:
                pretty = json.dumps(payload, indent=2)
            except TypeError:
                pretty = json.dumps({"data": str(payload)}, indent=2)
            st.success("JSON export ready.")
            st.code(pretty, language="json")
            st.download_button(
                "Download JSON",
                data=pretty,
                file_name=f"{invoice_id}.json",
                mime="application/json",
                key="download_json_btn",
            )
        else:
            if res.status_code != 200:
                st.error(response_payload(res))
                return
            st.success(f"{export_format.upper()} export ready.")
            if export_format == "csv":
                st.download_button(
                    "Download CSV",
                    data=res.content,
                    file_name=f"{invoice_id}.csv",
                    mime="text/csv",
                    key="download_csv_btn",
                )
            else:
                st.download_button(
                    "Download Excel",
                    data=res.content,
                    file_name=f"{invoice_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_btn",
                )


def render_history():
    render_section_intro(
        "History & Uploaded Files",
        "Refresh and filter invoice records to quickly find earlier uploads.",
    )
    if st.button("Refresh History", use_container_width=True, type="primary", key="refresh_history_btn"):
        res = get_json(f"{st.session_state.base_url}/invoices/list")
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        data = response_payload(res)
        if res.status_code == 200:
            st.session_state.history = data if isinstance(data, list) else []
        else:
            st.error(data)
            return

    history = st.session_state.history or []
    if not history:
        st.info("No history loaded yet. Click Refresh History.")
        return

    normalized_rows = [row if isinstance(row, dict) else {"value": row} for row in history]
    status_options = sorted(
        {
            str(row.get("processing_status") or row.get("status") or "unknown")
            for row in normalized_rows
        }
    )

    filter_col1, filter_col2 = st.columns([2, 1])
    with filter_col1:
        query = st.text_input("Search", key="history_search", placeholder="Invoice ID or filename")
    with filter_col2:
        selected_status = st.selectbox(
            "Status",
            ["All"] + status_options,
            key="history_status_filter",
        )

    query_text = query.strip().lower()
    filtered_rows = []
    for row in normalized_rows:
        row_status = str(row.get("processing_status") or row.get("status") or "unknown")
        if selected_status != "All" and row_status != selected_status:
            continue
        if query_text:
            haystack = " ".join(
                str(row.get(field, ""))
                for field in ("invoice_id", "filename", "processing_status", "status")
            ).lower()
            if query_text not in haystack:
                continue
        filtered_rows.append(row)

    st.caption(f"Showing {len(filtered_rows)} of {len(normalized_rows)} records.")
    st.dataframe(filtered_rows, use_container_width=True)


def main():
    st.set_page_config(page_title="Invoice Processing", layout="wide", initial_sidebar_state="collapsed")
    init_state()
    apply_futuristic_theme()
    render_main_header()
    st.caption("Operational workspace for invoice ingestion, extraction, human review, and export.")

    backend_ok, backend_status = check_backend(st.session_state.base_url)
    st.session_state.backend_ok = backend_ok
    st.session_state.backend_status = backend_status
    if not backend_ok:
        auto_start_backend()
        backend_ok, backend_status = check_backend(st.session_state.base_url)
        st.session_state.backend_ok = backend_ok
        st.session_state.backend_status = backend_status

    render_dashboard_panel(st.session_state.backend_ok, st.session_state.backend_status)

    if not st.session_state.get("backend_ok", False):
        st.error("Backend is offline. Start it on port 8000 and try again.")
        st.caption("Run: uvicorn backend.app.main:app --reload --port 8000")
        st.caption(f"Details: {st.session_state.get('backend_status')}")
        return

    tabs = st.tabs(["Upload", "Processing", "Review", "Export", "History"])
    with tabs[0]:
        render_upload()
    with tabs[1]:
        render_processing()
    with tabs[2]:
        render_review()
    with tabs[3]:
        render_export()
    with tabs[4]:
        render_history()


if __name__ == "__main__":
    main()
