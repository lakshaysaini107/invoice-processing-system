# invoiceflow

An AI-assisted invoice extraction platform that converts invoice PDFs/images into structured, reviewable, and exportable data.

## Project Details

### Why this project was developed

Invoice handling in many teams is still manual and error-prone:
- Teams retype invoice data into ERP/accounting tools.
- Different invoice formats make extraction inconsistent.
- Errors in GST, totals, dates, or vendor fields cause downstream finance issues.
- Manual review takes too long when done for every field.

This project was built to automate extraction while still keeping a human review step for accuracy and trust.

### How it helps

- Reduces manual entry effort by extracting key invoice fields automatically.
- Improves consistency using a defined processing and validation pipeline.
- Surfaces low-confidence fields for targeted manual review instead of reviewing everything.
- Keeps audit-friendly metadata such as corrections, review status, and processing state.
- Exports data to JSON/CSV/Excel for easy integration with finance workflows.

## Core Functionality

1. User authentication and access control
- Register/login with JWT-based auth.
- Password hashing and token verification.

2. Invoice upload and validation
- Accepts PDF, JPG, PNG, TIFF uploads.
- Validates format and file size before processing.
- Stores file metadata and processing state.

3. End-to-end processing pipeline
- Image preprocessing (deskew, denoise, contrast, sharpening).
- OCR extraction (PaddleOCR with Tesseract fallback).
- Layout detection for table/text structure.
- Field extraction using rule-based invoice heuristics.
- Named entity extraction and validation confidence scoring.

4. Human-in-the-loop review
- Fetch extracted invoice details for review.
- Submit corrections, notes, and approval/rejection.
- Persist corrections and final reviewed state.

5. Export and reporting
- Export single/batch invoice output in JSON, CSV, or Excel.
- Include extracted fields and processing metadata.

6. History and status tracking
- Track processing progress by invoice.
- List uploaded invoices with status and timestamps.

## Tech Stack and Why It Is Used

| Technology | Functionality in this project | Why it is used |
| --- | --- | --- |
| FastAPI | REST APIs for auth, upload, processing, review, export | High performance async framework, clean API design, built-in OpenAPI docs |
| Uvicorn | ASGI server for backend runtime | Fast and production-ready server for FastAPI |
| Pydantic / pydantic-settings | Request/response schemas and environment config | Strong validation, typed contracts, safer config handling |
| Streamlit | Frontend UI (`frontend.py`) for upload, review, and export workflows | Rapid UI development with minimal overhead for internal tools |
| MySQL + `aiomysql` | Persistent storage for users, invoices, status, extracted JSON blobs | Reliable relational storage with async DB access |
| JWT (`python-jose`) + Passlib (bcrypt) | Authentication tokens and password hashing | Standard secure auth pattern for API systems |
| OpenCV + NumPy | Image preprocessing and layout analysis | Efficient document image operations for OCR quality improvements |
| Tesseract (`pytesseract`) + PaddleOCR | OCR text extraction from invoice documents | Combines broad compatibility with stronger OCR on complex layouts |
| PyMuPDF | PDF page rendering before OCR | Converts PDFs to high-resolution images for better extraction |
| spaCy | NER for vendor/person/location and text entity support | Mature NLP library with ready-to-use NER pipeline |
| OpenPyXL | Excel export generation | Native `.xlsx` creation for finance-ready deliverables |
| Aiofiles + `python-multipart` | Async file upload and storage handling | Non-blocking upload flow and FastAPI multipart support |

## Processing Flow

1. Upload invoice file.
2. Create invoice record with `pending` status.
3. Run preprocessing and OCR.
4. Detect layout and extract structured fields.
5. Validate fields and assign confidence.
6. Mark processing `completed` or `failed`.
7. Review low-confidence fields manually (optional but recommended).
8. Export final output.
