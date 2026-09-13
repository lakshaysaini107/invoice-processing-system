# Project Structure

This document reflects the repository as it exists today, not the older placeholder layout.

## Actual Workspace Layout

```text
tdipl/
|-- backend/
|   |-- ai/
|   |   |-- confidence_scoring.py      # Alternate confidence engine
|   |   |-- layout_detection.py        # Table, text-region, and section detection
|   |   |-- ner_extraction.py          # spaCy + regex entity extraction
|   |   |-- ocr_engine.py              # PaddleOCR/Tesseract OCR engine
|   |   |-- preprocessing.py           # PDF rendering and image cleanup
|   |   |-- vision_llm.py              # Heuristic invoice field extraction
|   |-- api/
|   |   |-- auth.py                    # Register/login/me/logout APIs
|   |   |-- upload.py                  # Upload, list, delete invoice APIs
|   |   |-- process.py                 # Start/status/retry processing APIs
|   |   |-- review.py                  # Review details and correction submission
|   |   |-- export.py                  # JSON/CSV/Excel export APIs
|   |   |-- erp.py                     # ERP handoff and ERP save APIs
|   |-- app/
|   |   |-- config.py                  # Env-based settings
|   |   |-- dependencies.py            # Dependency wiring and current auth mode
|   |   |-- main.py                    # FastAPI entry point
|   |-- core/
|   |   |-- exceptions.py              # Shared HTTP exception helpers
|   |   |-- logging.py                 # Central logging setup
|   |   |-- security.py                # JWT + password hashing helpers
|   |-- database/
|   |   |-- mysql.py                   # Async MySQL connection and schema bootstrap
|   |   |-- repositories/
|   |       |-- user_repo.py           # User persistence
|   |       |-- invoice_repo.py        # Invoice persistence
|   |       |-- erp_invoice_repo.py    # ERP record persistence
|   |-- models/
|   |   |-- audit.py                   # Audit-related models
|   |   |-- inoice.py                  # Invoice models and enums
|   |   |-- user.py                    # User models
|   |-- services/
|   |   |-- upload_service.py          # File validation and storage
|   |   |-- processing_service.py      # End-to-end pipeline orchestrator
|   |   |-- review_service.py          # Correction merge helpers
|   |   |-- validation_service.py      # Field validation and confidence rules
|   |   |-- export_service.py          # JSON/CSV/Excel generation
|   |-- static/                        # Present but currently empty
|   |-- tests/
|   |   |-- conftest.py                # Async test fixtures and in-memory fakes
|   |   |-- test_api.py                # API route tests
|   |   |-- test_erp_api.py            # ERP route tests
|   |   |-- test_extraction.py         # Extraction pipeline tests
|   |   |-- test_ocr.py                # OCR tests
|   |   |-- test_security.py           # Hashing/token helper tests
|   |   |-- test_validation.py         # Validation tests
|   |-- utils/
|   |   |-- date_utils.py              # Date parsing/validation helpers
|   |   |-- gst_utils.py               # GST parsing/normalization helpers
|   |   |-- image_utils.py             # Generic image helpers
|   |   |-- math_utils.py              # Amount parsing helpers
|   |   |-- regex_utils.py             # Shared regex patterns
|   |-- requirements.txt               # Backend-only dependency list
|-- data/
|   |-- uploads/                       # Runtime upload storage
|   |-- local_db.json                  # Local artifact; not used by backend code
|-- logs/                              # Runtime log files
|-- api/                               # Local Python virtual environment
|-- accounting/                        # Currently unused local directory
|-- frontend.py                        # Main Streamlit invoice workflow UI
|-- erp_frontend.py                    # Separate Streamlit ERP handoff UI
|-- requirements.txt                   # Root dependency list for the whole project
|-- README.md                          # Main project documentation
|-- project_structure.md               # This file
|-- .env.example                       # Example environment variables
|-- .gitignore
```

## Runtime Notes

- `backend/models/inoice.py` is the active invoice model file even though the filename is misspelled.
- `api/` is not application source code; it is the checked-in local virtual environment used in this workspace.
- `data/` and `logs/` are runtime folders and are ignored by Git.
- `backend/static/` exists but is empty in the current project state.
- `.pytest_cache/`, `__pycache__/`, and similar generated folders are omitted from the tree above.

## Workflow Mapping

- `frontend.py` drives the user-facing path: upload, review, export, and ERP launch.
- `backend/api/process.py` and `backend/services/processing_service.py` drive the extraction pipeline.
- `backend/database/` persists invoice state and ERP records in MySQL.
- `erp_frontend.py` is the final ERP-entry surface after review/export handoff.
