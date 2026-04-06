# Invoiceflow - Intelligent Invoice Processing System

`invoiceflow` is a comprehensive, locally-run invoice processing platform that automates document extraction while maintaining human oversight. It accepts invoice PDFs or images, intelligently extracts structured fields with confidence scoring, flags uncertain values for human review, exports cleaned data in multiple formats, and integrates seamlessly with ERP-style systems.

## Core Purpose

The system bridges the gap between raw invoice documents and operational data entry. Instead of manual transcription, invoiceflow automatically extracts key invoice fields (invoice numbers, vendor details, amounts, tax information, line items, etc.) with built-in confidence scoring, allowing human reviewers to quickly validate and correct high-confidence extractions while focusing effort on uncertain fields.

## How It Works in 3 Steps

### 1. **Automatic Extraction**
User uploads a PDF or image → System automatically extracts invoice fields using local OCR, heuristics, and NLP → Extraction confidence is calculated for each field.

### 2. **Human Review & Correction**
Reviewer views extraction results with confidence indicators → Uncertain fields are highlighted → Reviewer corrects what needs fixing → System records all changes for audit trail.

### 3. **Export & Integration**
Cleaned data can be exported (JSON, CSV, Excel) for downstream systems → Or directly integrated into ERP forms with auto-filled fields → Complete lifecycle tracked in database.

The key innovation: **automation handles the routine work, confidence scores show where humans should focus, and the system remembers everything.**

## System Components

The complete system is built from:

- **FastAPI Backend**: Provides REST APIs for upload, processing, review, export, ERP integration, and authentication
- **Streamlit UI (frontend.py)**: Main operational interface with upload, review, and export workflows
- **ERP Integration (erp_frontend.py)**: Dedicated interface for final ERP-style data entry with auto-filled fields
- **MySQL Database**: Persistent storage for users, invoice metadata, extraction results, corrections, and ERP records
- **Local AI Pipeline**: OCR, layout detection, field extraction, and entity recognition without external APIs

## System Architecture

### Layered Architecture

The system follows a **three-tier layered architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                      │
│  Streamlit Frontend (frontend.py) | ERP UI (erp_frontend.py) │
│         (User Workflows & Manual Review)                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST Calls
                       ▼
┌──────────────────────────────────────────────────────────┐
│                    API LAYER                             │
│                 FastAPI Backend                          │
│  ┌─────────────┬────────────┬────────────┬───────────┐   │
│  │Auth API     │Upload API  │Process API │Review API │   │
│  │Export API   │ERP API     │Health API  │           │   │
│  └─────────────┴────────────┴────────────┴───────────┘   │
└──────────────┬───────────────────────────────────────────┘
               │ SQL Queries     
               ▼
┌──────────────────────────────────────────────────────────┐
│                   DATA LAYER                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           MySQL Relational Database                │ │
│  │   users | invoices | erp_invoices | audit records  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │        File Storage (data/uploads/<user_id>/)       │ │
│  │     (PDF, images, processing artifacts)             │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Processing Pipeline Architecture

The invoice processing happens asynchronously through multiple specialized stages:

```
Raw Invoice
    │
    ▼
┌─────────────────────────────────────────┐
│  PREPROCESSING                          │
│  • PDF → Images (PyMuPDF)                │
│  • Image Enhancement                    │
│  • Deskew, Denoise, Contrast, Sharpen  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  OCR EXTRACTION                         │
│  • PaddleOCR (Primary)                   │
│  • Tesseract (Fallback)                  │
│  • Multiple page segmentation modes     │
│  • Text + Bounding boxes captured       │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  LAYOUT DETECTION                       │
│  • Identify tables, text blocks          │
│  • Detect header/body/footer sections   │
│  • OpenCV morphology & contour analysis │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  FIELD EXTRACTION                       │
│  • Heuristic parser (vision_llm.py)     │
│  • Extract: invoice #, dates, vendor,   │
│    amounts, tax, PO, bank, line items   │
│  • No external API required              │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  ENTITY RECOGNITION                     │
│  • spaCy NER (organizations, people)     │
│  • Regex-based amount/date extraction   │
│  • Additional semantic context           │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  VALIDATION & CONFIDENCE SCORING        │
│  • Normalize dates, amounts, GST        │
│  • Validate payment terms, bank details │
│  • Field-level confidence scores        │
│  • Overall processing confidence        │
└─────────────────────────────────────────┘
    │
    ▼
Extracted Data with Confidence Metadata
(Ready for Human Review)
```

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

## Technology Stack & Architecture

### Backend & API Layer
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| API Framework | **FastAPI** | Defines all REST endpoints (upload, process, review, export, ERP) | Modern async support, automatic API documentation, strong type hints with Pydantic integration |
| ASGI Server | **Uvicorn** | Runs the FastAPI application | Lightweight, fast startup, perfect for local development and deployment |
| Async Task Queue | **FastAPI Background Tasks** | Runs invoice processing asynchronously | Simple to set up, integrated with FastAPI, sufficient for standard concurrent workloads |

### Frontend Layer
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| Main UI Framework | **Streamlit** | Powers main workflow UI (frontend.py) and ERP UI (erp_frontend.py) | Rapid development with minimal boilerplate, session state management, instant hot-reload |
| HTTP Client | **requests** | Frontend-to-backend communication | Simple, mature, reliable for local HTTP calls |

### Database & Storage
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| Relational Database | **MySQL** | Stores users, invoices, extracted data, corrections, ERP records, audit trail | Durable, relational schema supports complex queries, widely available |
| Async DB Driver | **aiomysql** | Non-blocking database access from async code | Prevents backend blocking, enables concurrent invoice processing |
| File Storage | **Filesystem** (data/uploads/) | Stores uploaded PDFs, images, and processing artifacts | Fast, simple, avoids database bloat for large files |

### Configuration & Security
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| Config Validation | **Pydantic** + **pydantic-settings** | Loads and validates `.env` settings at startup | Type-safe configuration, automatic environment variable binding, clear error messages |
| Password Hashing & JWT | **python-jose** + **bcrypt** + custom PBKDF2 | Handles authentication and session tokens | Industry-standard security primitives, supports legacy password migration |

### Document Processing (Image & PDF)
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| PDF Rendering | **PyMuPDF (fitz)** | Converts PDF pages to high-quality images | Fast rendering, accurate DPI handling, better OCR input than direct PDF text extraction |
| Image Enhancement | **OpenCV** + **NumPy** | Preprocessing: deskew, denoise, contrast, sharpen | Mature, optimized algorithms for document image processing |
| OCR Engine (Primary) | **PaddleOCR** | Fast, accurate OCR with bounding boxes | Modern deep learning OCR, 80+ languages, fast inference |
| OCR Engine (Fallback) | **Tesseract** | Text extraction with multiple segmentation modes | Reliable fallback, configurable page segmentation modes |
| Layout Analysis | **OpenCV** morphology & contours | Detects tables, text blocks, and document structure | Local processing, no external APIs, reveals document structure for extraction hints |

### NLP & Entity Extraction
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| Named Entity Recognition | **spaCy** (en_core_web_sm) | Identifies companies, people, locations in extracted text | Pre-trained model adds semantic understanding beyond regex, optional but enhances extraction |
| Business Logic | **Custom utils** (regex, validation) | Extracts and validates GST, dates, amounts, payment terms, bank details | Domain-specific rules ensure correctness for Indian invoices and financial data |

### Data Export & Reporting
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| Excel Generation | **openpyxl** | Creates `.xlsx` files with extracted data | Rich formatting support, batch export capability |
| CSV & JSON | **Python stdlib** (csv, json) | Standard text-based exports | Built-in, no dependencies, universal compatibility |

### Testing & Quality
| Component | Technology | Purpose | Why Chosen |
| --- | --- | --- | --- |
| Test Framework | **pytest** + **pytest-asyncio** | Unit and integration tests for all components | Strong async support, fixtures, parametrization |
| HTTP Client (Testing) | **httpx** | Test API endpoints with async support | Async-compatible, mirrors requests API |

### Why This Stack?

**Local-First Approach**: All core AI/ML components (OCR, NLP, image processing) run locally. No external APIs means lower latency, zero API costs, complete data privacy, and resilience to network issues.

**Scalability within Constraints**: FastAPI + async IO + aiomysql support concurrent invoice processing. Background tasks handle long-running extraction without blocking the UI.

**Maintainability**: Python-only stack eliminates language switching. Type hints, strong testing, and clear module separation make debugging and extension straightforward.

**Deployment Simplicity**: Single Python environment, auto-generated database schema, and integrated server startup reduce deployment friction.

## Benefits & Key Advantages

### Automation & Efficiency
- **Reduces Manual Data Entry**: Automates the repetitive first pass of data extraction, eliminating hours of manual invoice transcription
- **Batch Processing**: Process multiple invoices simultaneously with background task scheduling
- **Fast Extraction**: Local pipeline processes invoices in seconds without API latency or network dependency
- **Adaptive OCR**: Dual-engine OCR (PaddleOCR + Tesseract fallback) adapts to varying invoice quality and layout formats

### Human-Centric Design
- **Confidence Transparency**: Every extracted field includes a confidence score, showing where automation succeeded and where human judgment is needed
- **Low-Confidence Flagging**: Uncertain fields are automatically highlighted for human review rather than accepted blindly
- **Easy Corrections**: Reviewers can directly edit extracted JSON with instant validation feedback
- **Full Audit Trail**: Every correction, reviewer identity, and timestamp is recorded for compliance and learning

### Technical Advantages
- **No External API Dependencies**: All core processing uses local Python libraries—no reliance on cloud APIs, no API keys to manage, no latency concerns
- **Data Privacy**: Invoice documents and extracted data never leave your infrastructure
- **Scalable Architecture**: Async/await design with FastAPI background tasks supports multiple concurrent processing streams
- **Type Safety**: Pydantic models enforce data structure validation throughout the pipeline

### Business Intelligence & Integration
- **Multiple Export Formats**: Export extracted data as JSON, CSV, or Excel for easy downstream integration
- **ERP Integration**: Direct handoff to ERP systems via dedicated ERP form with auto-filled fields
- **Database Persistence**: Complete invoice lifecycle stored in MySQL—track progress, view OCR artifacts, run analytics
- **Metadata Richness**: Stores OCR results, layout info, extracted entities, and corrections for auditing and machine learning feedback

### Operational Flexibility
- **Flexible Input**: Accepts PDF, JPG, PNG, and TIFF files; ZIP uploads are automatically unpacked
- **Modular Pipeline**: Each processing stage (preprocessing, OCR, extraction, validation) can be adjusted or extended independently
- **Auto-Schema Creation**: Database tables are created automatically on startup, reducing deployment friction
- **Graceful Fallbacks**: PaddleOCR falls back to Tesseract; spaCy NER is optional but enhances results when available

## Data Flow & Lifecycle

Understanding how information flows through the system reveals its power and design philosophy:

### Complete Invoice Lifecycle

```
1. UPLOAD
   ├─ User uploads PDF/image files via Streamlit
   ├─ Backend validates file type & size
   ├─ Files stored in data/uploads/<user_id>/
   └─ MySQL invoice record created (status: pending)

2. PROCESSING (Async Background Task)
   ├─ Preprocessing: PDF → images, enhance quality
   ├─ OCR: Extract text + bounding boxes
   ├─ Layout: Detect tables, text blocks, sections
   ├─ Field Extraction: Parse vendor, amounts, dates, etc.
   ├─ Entity Recognition: Identify organizations, people
   ├─ Validation: Normalize data, compute confidence scores
   └─ All intermediate results stored in MySQL

3. REVIEW (Human-in-the-Loop)
   ├─ Frontend polls processing status
   ├─ When ready, displays extracted JSON + confidence
   ├─ Reviewer edits uncertain fields
   ├─ Frontend marks corrections and submits
   └─ MySQL updated with corrected data (status: reviewed)

4. EXPORT
   ├─ Export as JSON (raw extraction)
   ├─ Export as CSV (flattened rows)
   ├─ Export as Excel (formatted workbook)
   └─ No database required; data is self-contained

5. ERP INTEGRATION
   ├─ User launches ERP form from main UI
   ├─ ERP UI auto-fills from extraction
   ├─ User edits and saves ERP record
   └─ Data persisted in erp_invoices table
```

### Key Data Artifacts Stored

For each invoice, the system maintains:

- **extracted_data**: Final JSON with all fields (invoice #, vendor, amounts, line items, etc.)
- **confidence_scores**: Field-level and overall confidence metrics from extraction
- **ocr_result**: Raw OCR text and character-level bounding boxes
- **layout_info**: Detected document structure (tables, text blocks, regions)
- **entities**: Named entities identified by spaCy
- **corrections**: Journal of all human edits during review
- **audit_metadata**: Reviewer identity, timestamps, processing duration

This comprehensive storage enables:
- Compliance audits (who reviewed, when, what changed)
- ML feedback loops (understanding where extraction failed)
- Debugging (viewing intermediate results)
- Reprocessing (if algorithms improve)

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

## Use Cases & Real-World Workflows

### Typical User Scenarios

**Scenario 1: Accounts Payable Processor**
- Receives 50 vendor invoices daily
- Uploads batch to invoiceflow in ZIP
- System extracts vendor info, invoice #, amounts, PO reference, GST
- Reviews only fields with < 85% confidence (usually 10-20% of extractions)
- Exports corrected data to accounting system in 15 minutes instead of 2+ hours manual entry

**Scenario 2: Finance Manager**
- Needs to reconcile and record invoices in ERP
- Instead of copying invoice data field-by-field, launches ERP form
- Form auto-fills vendor details, amounts, payment terms from extraction
- Makes final adjustments and saves to ERP_invoices table
- Can download CSV for further processing

**Scenario 3: Audit & Compliance**
- Needs to verify all invoice entries and who approved them
- Queries MySQL database for complete audit trail
- Sees original extraction, reviewer corrections, and timestamps
- Can trace extraction confidence scores back to raw OCR for disputed fields

**Scenario 4: High-Volume Processing**
- Small business processes 200+ invoices monthly
- Extracts overnight as batch with background tasks
- Next morning, reviews corrections in batches by vendor
- Exports final data directly to CSV for bank transfer file generation

### When invoiceflow Shines

✅ **High volume of similar document types** (lots of vendor invoices)  
✅ **Documents with varying quality** (mix of scanned and digital)  
✅ **Compliance requirement for audit trails** (need to prove who checked what)  
✅ **Repeated data entry into ERP systems** (auto-fill saves hours)  
✅ **No external API access or offline requirements** (local-only processing)  
✅ **Need for transparency** (confidence scores show automation limits)

### When to Consider Alternatives

❌ Single, one-off documents (overhead not justified)  
❌ Highly specialized or non-standard formats (extraction may need custom rules)  
❌ Real-time requirements with sub-second processing (async design expects human review)  
❌ Extreme document complexity (layout detection may struggle with multi-column highly artistic layouts)

## Important Current Caveats

- Authentication helpers and auth endpoints exist, but `backend/app/dependencies.py` currently returns a hardcoded public admin user context. In practice, the current build behaves as an open demo environment.
- `backend/ai/vision_llm.py` is a heuristic extractor, not a live LLM integration.
- The legacy ERP handoff store is still in memory, but the ERP UI can now load a selected invoice directly by invoice ID when launched from the main app.
- Processing runs in FastAPI background tasks, not in a separate job queue or worker system.
- The main frontend exposes a `use_cache` option, but the current processing service does not implement cache reuse logic.
- `data/local_db.json` exists in the workspace but is not part of the active backend persistence path.

## Project Map

See `project_structure.md` for the current repository layout and folder-by-folder explanation.

## Extending & Customizing the System

The modular design makes invoiceflow easy to extend for specific needs:

### Common Customizations

**Adding Extra Invoice Fields**
1. Update the extraction heuristics in `backend/ai/vision_llm.py` to parse new fields from OCR text
2. Add validation rules to `backend/utils/` or `backend/services/validation_service.py`
3. Update Pydantic models in `backend/models/` to include new fields
4. Frontend automatically displays new fields in review UI

**Improving OCR Quality**
- Preprocessing parameters (deskew threshold, contrast levels) are tunable in `backend/ai/preprocessing.py`
- OCR engine selection and fallback logic in `backend/ai/ocr_engine.py`
- Page segmentation modes for Tesseract can be adjusted based on document layout

**Adding Custom Business Rules**
- Create new validators in `backend/services/validation_service.py`
- Add field-level confidence rules based on your specific requirements
- Heuristic extraction in `backend/ai/vision_llm.py` can be expanded with regex or pattern matching

**Connecting to External Systems**
- Add export endpoints in `backend/api/export.py` for your target systems
- Extend ERP API `backend/api/erp.py` to call external ERP APIs
- Use the complete invoice lifecycle stored in MySQL as a source

**Improving Entity Recognition**
- Replace the optional spaCy model with domain-specific training
- Add custom regex patterns for business entities in `backend/ai/ner_extraction.py`
- Leverage the stored `entities` field in MySQL for feedback loops

### Architecture For Scaling

**For Higher Volumes**
- Replace FastAPI background tasks with Celery + Redis
- Configure MySQL connection pooling in `backend/database/mysql.py`
- Add caching layer (e.g., Redis) for processed OCR results
- Deploy backend on dedicated server, frontends separately

**For ML Improvements**
- Use stored confidence scores and corrections as training data
- Fine-tune models on your specific invoice formats
- A/B test extraction algorithms using the audit trail
- Build feedback loop: corrections → retrain → deploy

**For Production Deployment**
- Implement the auth system in `backend/app/dependencies.py` with real user management
- Add request logging and monitoring (`backend/core/logging.py`)
- Run multiple Uvicorn workers behind a reverse proxy (nginx/HAProxy)
- Use Docker for consistent deployment across environments
- Set up database backups and point-in-time recovery

### Development Tips

- **Test Locally First**: Run `pytest` to validate changes before deployment
- **Check Confidence Scores**: Review extracted confidence metrics by device type or vendor to spot patterns
- **Use MySQL Audit Trail**: Query correction history to find extraction weaknesses
- **Iterate on Validation**: Start with strict validation, then relax rules based on real failure patterns
- **Leverage Intermediate Results**: Use stored `ocr_result` and `layout_info` to debug extraction issues
