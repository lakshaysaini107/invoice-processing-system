# Invoiceflow - Intelligent Invoice Processing System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Deployment](https://img.shields.io/badge/Deploy-Render%20Docker-46E3B7.svg)](https://render.com/)

`invoiceflow` is a portfolio-ready, intelligent invoice processing platform that automates document data extraction while maintaining human oversight. It ingests invoice PDFs or images, extracts key financial fields with confidence scoring, flags uncertain values for human review, exports structured data (JSON, CSV, Excel), and integrates with ERP forms.

---

## Portfolio Quick Links
- **Live Demo Platform**: `https://<your-render-app-name>.onrender.com` *(Update with deployed Render URL)*
- **Architecture**: 3-Tier Layered Architecture (FastAPI + Streamlit + Resilient MySQL/SQLite Persistence)
- **Deployment Platform**: Render Free Tier (via Containerized Dockerfile)

---

## Core Features & Workflow

### 1. **Automated Extraction Pipeline**
- Supports PDF, PNG, JPG, and TIFF invoices (with automatic ZIP unpack).
- Document image preprocessing: deskewing, CLAHE contrast enhancement, and denoising.
- Dual-Engine OCR: PaddleOCR support with lightweight Tesseract OCR fallback.
- Layout detection: table region segmentation & document structure analysis.
- Field extraction: invoice number, dates, vendor/buyer info, GSTINs, amounts, tax calculations, bank details (account #, IFSC), and line items.

### 2. **Human-in-the-Loop Review**
- Field-level confidence scores highlight uncertain values for rapid validation.
- Interactive JSON editing and correction submission.
- Complete audit logging of reviewer changes.

### 3. **Export & ERP Handoff**
- Multi-format export: JSON, CSV, and formatted `.xlsx` Excel spreadsheets.
- Direct ERP integration with auto-filled entry forms (`erp_frontend.py`).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                      │
│  Streamlit Frontend (frontend.py) | ERP UI (erp_frontend.py) │
│         (User Workflows & Manual Review)                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / REST Calls
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    API LAYER                             │
│                 FastAPI Backend                          │
│  ┌─────────────┬────────────┬────────────┬───────────┐   │
│  │Auth API     │Upload API  │Process API │Review API │   │
│  │Export API   │ERP API     │Health API  │           │   │
│  └─────────────┴────────────┴────────────┴───────────┘   │
└──────────────┬───────────────────────────────────────────┘
               │ SQL Queries (MySQL / SQLite Fallback)
               ▼
┌──────────────────────────────────────────────────────────┐
│                   DATA LAYER                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Relational Storage (MySQL / SQLite)       │ │
│  │   users | invoices | erp_invoices | audit records  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │        File Storage (data/uploads/<user_id>/)       │ │
│  │     (PDF, images, processing artifacts)             │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Default Value | Description |
| --- | --- | --- |
| `APP_NAME` | `Invoice Processing System` | Application display name |
| `ENVIRONMENT` | `development` | Environment mode (`development` / `production`) |
| `AUTH_DISABLED` | `true` | Enables open demo mode for portfolio showcase |
| `MYSQL_HOST` | `localhost` | MySQL host address (falls back to SQLite if unreachable) |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_DATABASE` | `invoices` | Target database name |
| `MYSQL_USER` | `root` | Database user |
| `MYSQL_PASSWORD` | `""` | Database password |
| `SECRET_KEY` | `your-super-secret-key...` | JWT token signing key |

---

## Local Setup & Quickstart

### 1. Initialize Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Automated Test Suite
```powershell
pytest backend/tests
```

### 4. Launch Services Locally
- **Backend API Server (Port 8000)**:
  ```powershell
  python -m uvicorn backend.app.main:app --reload --port 8000
  ```
- **Main Workflow UI (Port 8501)**:
  ```powershell
  streamlit run frontend.py
  ```
- **ERP Integration UI (Port 8503)**:
  ```powershell
  streamlit run erp_frontend.py --server.port 8503
  ```

---

## Public Cloud Deployment Guide (Render Free Tier)

### Why Render (Docker Container) over Vercel?
Streamlit applications require a long-running Python process with active WebSocket connections and C-binary dependencies (`tesseract-ocr`, `libglib2.0`, `PyMuPDF`). Serverless platforms like Vercel do not support persistent processes or system-level apt packages. **Render Web Services (Free Tier via Docker)** is the recommended deployment host.

### Deployment Steps on Render
1. Push repository to GitHub.
2. Log in to [Render](https://render.com/) and click **New > Blueprint**.
3. Connect your GitHub repository (Render detects `render.yaml` automatically).
4. Render builds the container using `Dockerfile` and deploys the unified service.
5. Open your live deployment URL!

---

## License
MIT License
