import io
import json
import mimetypes
import subprocess
import sys
import time
import zipfile
from typing import List, Tuple, Optional

import requests
from requests.exceptions import RequestException
import streamlit as st


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
    st.subheader("Upload Invoices")
    auto_process = st.checkbox("Auto-start processing after upload", value=True)
    use_cache = st.checkbox("Use cache for processing", value=True)
    mode = st.radio("Upload Mode", ["Batch files", "Folder (zip)"], horizontal=True)

    if mode == "Batch files":
        files = st.file_uploader(
            "Select files (PDF/JPG/PNG/TIFF)",
            type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
            accept_multiple_files=True,
        )
        if st.button("Upload Selected Files", use_container_width=True):
            if not files:
                st.warning("Please select at least one file.")
                return
            results = []
            for f in files:
                res = upload_single_file(
                    st.session_state.base_url,
                    f.name,
                    f.getvalue(),
                    f.type or "application/octet-stream",
                )
                if isinstance(res, dict) and res.get("_error"):
                    results.append({"file": f.name, "status": "error", "data": res["_error"]})
                    continue
                try:
                    data = res.json()
                except Exception:
                    data = {"error": res.text}
                process_info = None
                invoice_id = data.get("invoice_id") if isinstance(data, dict) else None
                if invoice_id:
                    st.session_state.last_uploads.append(invoice_id)
                if auto_process and res.status_code == 200 and invoice_id:
                    proc_res = post_json(
                        f"{st.session_state.base_url}/process/start",
                        {"invoice_id": invoice_id, "use_cache": use_cache},
                    )
                    if isinstance(proc_res, dict) and proc_res.get("_error"):
                        process_info = {"error": proc_res["_error"]}
                    else:
                        try:
                            process_info = proc_res.json()
                        except Exception:
                            process_info = {"error": proc_res.text}
                results.append(
                    {
                        "file": f.name,
                        "status": res.status_code,
                        "data": data,
                        "processing": process_info,
                    }
                )
            st.write(results)

    else:
        zip_file = st.file_uploader("Upload a .zip file containing invoices", type=["zip"])
        if st.button("Upload Zip Contents", use_container_width=True):
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
            results = []
            for name, content, mime in extracted:
                res = upload_single_file(st.session_state.base_url, name, content, mime)
                if isinstance(res, dict) and res.get("_error"):
                    results.append({"file": name, "status": "error", "data": res["_error"]})
                    continue
                try:
                    data = res.json()
                except Exception:
                    data = {"error": res.text}
                process_info = None
                invoice_id = data.get("invoice_id") if isinstance(data, dict) else None
                if invoice_id:
                    st.session_state.last_uploads.append(invoice_id)
                if auto_process and res.status_code == 200 and invoice_id:
                    proc_res = post_json(
                        f"{st.session_state.base_url}/process/start",
                        {"invoice_id": invoice_id, "use_cache": use_cache},
                    )
                    if isinstance(proc_res, dict) and proc_res.get("_error"):
                        process_info = {"error": proc_res["_error"]}
                    else:
                        try:
                            process_info = proc_res.json()
                        except Exception:
                            process_info = {"error": proc_res.text}
                results.append(
                    {
                        "file": name,
                        "status": res.status_code,
                        "data": data,
                        "processing": process_info,
                    }
                )
            st.write(results)


def render_processing():
    st.subheader("Processing")
    invoice_id = st.text_input("Invoice ID", key="process_id")
    use_cache = st.checkbox("Use cache when available", value=True, key="process_cache")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Processing", use_container_width=True):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            payload = {"invoice_id": invoice_id, "use_cache": use_cache}
            res = post_json(f"{st.session_state.base_url}/process/start", payload)
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            try:
                data = res.json()
            except Exception:
                data = {"error": res.text}
            if res.status_code == 200:
                st.success(data.get("message", "Processing started"))
                st.session_state.process_status = data
            else:
                st.error(data)
    with col2:
        if st.button("Check Status", use_container_width=True):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            res = get_json(f"{st.session_state.base_url}/process/status/{invoice_id}")
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            try:
                data = res.json()
            except Exception:
                data = {"error": res.text}
            if res.status_code == 200:
                st.session_state.process_status = data
            else:
                st.error(data)

    status = st.session_state.process_status
    if status:
        progress = status.get("progress", 0)
        st.progress(progress / 100 if isinstance(progress, (int, float)) else 0)
        st.write(f"Status: {status.get('status')}")
        st.write(f"Current Step: {status.get('current_step')}")
        if status.get("error_message"):
            st.error(status.get("error_message"))
        if status.get("extracted_data"):
            st.json(status.get("extracted_data"))


def render_review():
    st.subheader("Manual Review")
    invoice_id = st.text_input("Invoice ID", key="review_id")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Details", use_container_width=True):
            if not invoice_id:
                st.warning("Please enter an invoice ID.")
                return
            res = get_json(f"{st.session_state.base_url}/review/{invoice_id}/details")
            if isinstance(res, dict) and res.get("_error"):
                st.error(f"Backend not reachable: {res['_error']}")
                return
            try:
                data = res.json()
            except Exception:
                data = {"error": res.text}
            if res.status_code == 200:
                st.session_state.review_details = data
                st.session_state.review_json = json.dumps(
                    data.get("extracted_data", {}),
                    indent=2
                )
            else:
                st.error(data)
    with col2:
        if st.button("Clear Review", use_container_width=True):
            st.session_state.review_details = None
            st.session_state.review_json = ""

    details = st.session_state.review_details
    if not details:
        st.info("Load invoice details to review extracted data.")
        return

    if details.get("invoice_id") != invoice_id:
        st.info("Loaded details do not match the current invoice ID. Reload details.")
        return

    st.write(f"Filename: {details.get('filename')}")
    st.write(f"Processing Status: {details.get('processing_status')}")
    confidence_scores = details.get("confidence_scores", {})
    if confidence_scores:
        st.json(confidence_scores)

    edited_json = st.text_area(
        "Extracted Data (JSON)",
        key="review_json",
        height=300
    )
    notes = st.text_area("Review Notes", key="review_notes")
    approved = st.checkbox("Approve invoice", value=True, key="review_approved")

    if st.button("Submit Review", use_container_width=True):
        if not invoice_id:
            st.warning("Please enter an invoice ID.")
            return
        try:
            edited_data = json.loads(edited_json) if edited_json.strip() else {}
        except Exception as e:
            st.error(f"Invalid JSON: {e}")
            return

        original_data = details.get("extracted_data", {})
        corrections = []
        for key in set(original_data.keys()) | set(edited_data.keys()):
            original_value = original_data.get(key)
            corrected_value = edited_data.get(key)
            if corrected_value != original_value:
                corrections.append(
                    {
                        "field_name": key,
                        "original_value": original_value,
                        "corrected_value": corrected_value,
                        "confidence": confidence_scores.get(key, {}).get("confidence"),
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
        try:
            data = res.json()
        except Exception:
            data = {"error": res.text}
        if res.status_code == 200:
            st.success(f"Review submitted: {data}")
        else:
            st.error(data)


def render_export():
    st.subheader("Export")
    invoice_id = st.text_input("Invoice ID", key="export_id")
    export_format = st.selectbox("Format", ["json", "csv", "excel"], key="export_format")
    if st.button("Export", use_container_width=True):
        if not invoice_id:
            st.warning("Please enter an invoice ID.")
            return
        url = f"{st.session_state.base_url}/export/single/{invoice_id}?format={export_format}"
        res = post_json(url)
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        if export_format == "json":
            try:
                data = res.json()
            except Exception:
                st.error(res.text)
                return
            if res.status_code != 200:
                st.error(data)
                return
            payload = data.get("data", data) if isinstance(data, dict) else data
            pretty = json.dumps(payload, indent=2)
            st.code(pretty, language="json")
            st.download_button(
                "Download JSON",
                data=pretty,
                file_name=f"{invoice_id}.json",
                mime="application/json",
            )
        else:
            if res.status_code != 200:
                try:
                    data = res.json()
                except Exception:
                    data = res.text
                st.error(data)
                return
            if export_format == "csv":
                st.download_button(
                    "Download CSV",
                    data=res.content,
                    file_name=f"{invoice_id}.csv",
                    mime="text/csv",
                )
            else:
                st.download_button(
                    "Download Excel",
                    data=res.content,
                    file_name=f"{invoice_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )


def render_history():
    st.subheader("History & Uploaded Files")
    if st.button("Refresh History", use_container_width=True):
        res = get_json(f"{st.session_state.base_url}/invoices/list")
        if isinstance(res, dict) and res.get("_error"):
            st.error(f"Backend not reachable: {res['_error']}")
            return
        try:
            data = res.json()
        except Exception:
            data = []
        if res.status_code == 200:
            st.session_state.history = data
        else:
            st.error(data)
            return

    history = st.session_state.history or []
    if history:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("No history loaded yet. Click Refresh History.")


def main():
    init_state()

    st.set_page_config(page_title="Invoice Processing", layout="wide")
    st.title("Invoice Processing Dashboard")

    # Auto-start backend on app launch if needed
    backend_ok, backend_status = check_backend(st.session_state.base_url)
    st.session_state.backend_ok = backend_ok
    st.session_state.backend_status = backend_status
    if not backend_ok:
        auto_start_backend()
        backend_ok, backend_status = check_backend(st.session_state.base_url)
        st.session_state.backend_ok = backend_ok
        st.session_state.backend_status = backend_status

    with st.sidebar:
        st.header("Backend")
        st.session_state.base_url = st.text_input("API Base URL", st.session_state.base_url)
        backend_ok, backend_status = check_backend(st.session_state.base_url)
        st.session_state.backend_ok = backend_ok
        st.session_state.backend_status = backend_status
        if not backend_ok:
            auto_start_backend()
            backend_ok, backend_status = check_backend(st.session_state.base_url)
            st.session_state.backend_ok = backend_ok
            st.session_state.backend_status = backend_status
        if backend_ok:
            st.success("Backend reachable")
        else:
            st.warning("Backend offline")
            st.caption(f"Details: {backend_status}")
            if st.session_state.backend_proc and st.session_state.backend_proc.poll() is not None:
                st.caption(f"Backend process exited with code {st.session_state.backend_proc.returncode}")
            if st.button("Start Backend", use_container_width=True):
                ok, msg = start_backend_process()
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
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
