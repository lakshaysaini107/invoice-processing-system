# invoiceflow

`invoiceflow` is a local invoice-processing system that accepts invoice PDFs or images, extracts structured fields, flags uncertain values for human review, exports the cleaned result, and can hand the reviewed invoice into an ERP-style entry form.

## What The System Includes

- A `FastAPI` backend for upload, processing, review, export, ERP handoff, and health endpoints.
- A main `Streamlit` app in `frontend.py` for the operational workflow.
- A second `Streamlit` app in `erp_frontend.py` for final ERP-style data entry.
- A `MySQL` persistence layer that stores users, invoice lifecycle data, extracted payloads, and ERP records.
- An OCR and extraction pipeline built from local Python libraries rather than a hosted AI API.

## Full System Workflow

### 1. Application Startup

When the backend starts, `backend/app/main.py` loads settings from `.env`, connects to MySQL through `backend/database/mysql.py`, and automatically creates the required tables if they do not exist yet:

- `users`
- `invoices`
- `erp_invoices`

The API then exposes:

- `/health`
- `/api/auth/*`
- `/api/invoices/*`
- `/api/process/*`
- `/api/review/*`
- `/api/export/*`
- `/api/erp/*`

### 2. Frontend Startup

The main Streamlit UI in `frontend.py` initializes session state, checks whether the backend is reachable, and can auto-start Uvicorn if the backend is offline. The user-facing workflow is centered around three tabs:

- `Upload`
- `Review`
- `Export`

The ERP form runs separately from `erp_frontend.py`.

### 3. Upload Flow

The upload path works like this:

1. A user uploads PDF, JPG, PNG, or TIFF files from the Streamlit UI.
2. ZIP uploads are unpacked in the Streamlit layer and then uploaded file-by-file to the backend.
3. `backend/api/upload.py` validates each file through `UploadService`.
4. `UploadService` checks MIME type and file size, then saves the file into `data/uploads/<user_id>/`.
5. `InvoiceRepository` creates a MySQL record with:
   - invoice ID
   - filename
   - file path
   - file size
   - upload timestamp
   - `processing_status = pending`

At that point the invoice exists in storage and is ready for extraction.

### 4. Processing Pipeline

Processing is triggered through `/api/process/start`. The backend marks the invoice as `processing` and schedules a FastAPI background task that runs `ProcessingService.process_invoice()`.

The pipeline stages are:

1. `Preprocessing`
   - `backend/ai/preprocessing.py`
   - PDFs are rendered with `PyMuPDF`
   - Images are deskewed, denoised, contrast-enhanced, and sharpened
   - Benefit: better OCR quality on noisy scans and camera captures

2. `OCR`
   - `backend/ai/ocr_engine.py`
   - Uses `PaddleOCR` when the Paddle runtime is available
   - Falls back to `Tesseract` otherwise
   - Tesseract mode tries multiple image variants and page segmentation modes to choose the strongest result
   - Benefit: stronger extraction resilience across different invoice qualities and layouts

3. `Layout Detection`
   - `backend/ai/layout_detection.py`
   - Detects likely tables, text blocks, and simple header/body/footer sections using OpenCV morphology and contour logic
   - Benefit: keeps structural context available for later extraction and debugging

4. `Field Extraction`
   - `backend/ai/vision_llm.py`
   - Despite the file name, this is currently a heuristic extractor, not an external hosted LLM
   - It parses OCR text to identify invoice number, dates, vendor/buyer details, GST numbers, amounts, tax, PO number, bank details, and line items
   - Benefit: no API keys or remote inference service are required

5. `Entity Recognition`
   - `backend/ai/ner_extraction.py`
   - Uses `spaCy` when `en_core_web_sm` is installed
   - Adds regex-based amount and date extraction
   - Benefit: gives extra context for vendors, contacts, locations, dates, and amounts

6. `Validation`
   - `backend/services/validation_service.py`
   - Normalizes and validates dates, GST numbers, names, amounts, payment terms, and bank details
   - Produces field-level confidence metadata and an overall confidence score
   - Benefit: makes the output reviewable and allows targeted human correction

7. `Persistence`
   - `InvoiceRepository.update()` writes the final output back into MySQL
   - Stored artifacts include:
     - `extracted_data`
     - `confidence_scores`
     - `ocr_result`
     - `layout_info`
     - `entities`
     - status/progress metadata

### 5. Review Flow

The Review tab is the human-in-the-loop stage.

1. The frontend requests `/api/review/{invoice_id}/details`.
2. If processing is still running, the UI keeps polling and shows progress/current step.
3. Once the invoice is ready, the UI shows:
   - extracted JSON
   - confidence values
   - review notes
   - approval toggle
4. The reviewer edits the JSON directly.
5. The frontend computes changed fields as corrections and submits them to `/api/review/{invoice_id}/submit`.
6. `ReviewService` applies the corrections and the repository stores:
   - corrected `extracted_data`
   - `review_status`
   - `reviewed_by`
   - `reviewed_at`
   - correction list
   - review notes
   - `processing_status = reviewed`

This is the trust layer of the system: automation does the first pass, while the reviewer confirms or fixes the final business data.

### 6. Export Flow

The Export tab supports:

- JSON export
- CSV export
- Excel export

`backend/api/export.py` calls `ExportService`, which:

- formats a single invoice or batch into JSON payloads
- flattens extracted fields into CSV rows
- generates `.xlsx` files with `openpyxl`

This makes the extracted data usable outside the application without requiring direct database access.

### 7. ERP Handoff Flow

The ERP handoff is split into two parts:

1. From the main UI, the user clicks `Fill in ERP`.
2. The main UI opens the ERP app with the active backend URL and selected invoice ID in the launch URL.
3. `erp_frontend.py` loads that invoice directly through `/api/erp/invoice/{invoice_id}`.
4. The legacy `/api/erp/set_current_invoice` and `/api/erp/get_current_invoice` flow still exists as a fallback handoff path.
5. The ERP UI auto-fills fields such as invoice number, vendor details, buyer details, totals, tax, bank details, and line items.
6. A user can edit the ERP form and press `Save`.
7. `/api/erp/save_erp` writes the cleaned ERP record into the `erp_invoices` MySQL table.

This creates a bridge from document extraction into downstream finance/ERP entry.

## Tech Stack

| Layer | Technology | How it is used here | Benefit |
| --- | --- | --- | --- |
| API backend | FastAPI | Defines upload, processing, review, export, ERP, and auth endpoints | Clean async API design, strong typing, easy testing |
| ASGI server | Uvicorn | Runs the FastAPI app locally | Fast startup and simple local deployment |
| UI | Streamlit | Powers `frontend.py` and `erp_frontend.py` | Rapid internal-tool development with minimal boilerplate |
| Config | Pydantic + pydantic-settings | Loads `.env` values and validates settings | Safer configuration and cleaner environment handling |
| Database | MySQL + aiomysql | Stores invoice lifecycle records, users, and ERP saves | Durable relational storage with async access |
| File uploads | aiofiles + python-multipart | Handles async upload reads and multipart form parsing | Efficient file ingestion for invoice documents |
| OCR/image work | OpenCV + NumPy | Image preprocessing, thresholding, morphology, and layout logic | Strong local document-image processing performance |
| PDF rendering | PyMuPDF | Renders PDF pages into images before OCR | Better OCR-ready page images from source PDFs |
| OCR engines | PaddleOCR + Tesseract | Extract raw text and bounding boxes from invoices | Dual-engine flexibility improves robustness |
| NLP/entity extraction | spaCy | Extracts organizations, people, and locations when the model is installed | Adds semantic clues beyond raw regex extraction |
| Business validation | Custom utils/services | Validates GST, dates, amounts, payment terms, and bank fields | Improves correctness and highlights risky fields |
| Security helpers | python-jose + bcrypt + custom PBKDF2 logic | Supports JWT generation and password verification/hash migration | Keeps auth primitives available for secure deployments |
| Exports | openpyxl + csv/json stdlib | Produces Excel, CSV, and JSON outputs | Easy downstream sharing and reporting |
| Frontend-backend communication | requests | Streamlit apps call backend APIs | Simple and stable local HTTP integration |
| Testing | pytest + pytest-asyncio + httpx | Covers routes, OCR, validation, extraction, and ERP APIs | Safer refactoring and easier regression checks |

## Benefits Of This Design

- Reduces manual invoice entry by automating the first extraction pass.
- Keeps humans in control by surfacing low-confidence fields for correction instead of hiding uncertainty.
- Stores the full invoice lifecycle in MySQL, including progress, OCR output, corrections, and review metadata.
- Runs mostly with local Python components, so the core workflow does not depend on external AI APIs.
- Supports multiple output paths: review, export, and ERP-style persistence.
- Auto-creates the database schema on startup, which lowers setup friction.

## Running The Project

### 1. Create and activate an environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create `.env`

Copy `.env.example` to `.env` and set at least:

- `SECRET_KEY`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

Optional but useful:

- `MYSQL_URL`
- `TESSERACT_CMD`
- `TESSDATA_PREFIX`

### 4. Install optional local OCR/NLP extras

Recommended:

```powershell
python -m spacy download en_core_web_sm
```

If Tesseract is not on your `PATH`, install it and point `TESSERACT_CMD` to the executable.

### 5. Start the backend

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

### 6. Start the main workflow UI

```powershell
streamlit run frontend.py
```

### 7. Start the ERP UI

```powershell
streamlit run erp_frontend.py --server.port 8503
```

If your backend is not running on `http://localhost:8000/api`, set `ERP_BACKEND_API` before starting the ERP UI or update the backend URL from the ERP sidebar.

Example:

```powershell
$env:ERP_BACKEND_API = "http://localhost:8000/api"
streamlit run erp_frontend.py --server.port 8503
```

## Important Current Caveats

- Authentication helpers and auth endpoints exist, but `backend/app/dependencies.py` currently returns a hardcoded public admin user context. In practice, the current build behaves as an open demo environment.
- `backend/ai/vision_llm.py` is a heuristic extractor, not a live LLM integration.
- The legacy ERP handoff store is still in memory, but the ERP UI can now load a selected invoice directly by invoice ID when launched from the main app.
- Processing runs in FastAPI background tasks, not in a separate job queue or worker system.
- The main frontend exposes a `use_cache` option, but the current processing service does not implement cache reuse logic.
- `data/local_db.json` exists in the workspace but is not part of the active backend persistence path.

## Project Map

See `project_structure.md` for the current repository layout and folder-by-folder explanation.
