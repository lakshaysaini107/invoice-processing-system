invoice-processing-system/
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Environment & app config
│   │   ├── dependencies.py            # Dependency injection
│   │
│   │   ├── api/                       # API layer
│   │   │   ├── auth.py                # Authentication APIs
│   │   │   ├── upload.py              # Invoice upload
│   │   │   ├── process.py             # OCR + AI extraction trigger
│   │   │   ├── review.py              # Manual correction APIs
│   │   │   └── export.py              # JSON / CSV / Excel export
│   │
│   │   ├── core/                      # Core system logic
│   │   │   ├── security.py             # JWT, roles, permissions
│   │   │   ├── logging.py              # Central logging
│   │   │   └── exceptions.py           # Custom exceptions
│   │
│   │   ├── services/                  # Business services
│   │   │   ├── upload_service.py
│   │   │   ├── processing_service.py   # Orchestrates full pipeline
│   │   │   ├── validation_service.py   # Accuracy checks
│   │   │   ├── review_service.py       # Human-in-the-loop
│   │   │   └── export_service.py
│   │
│   │   ├── ai/                        # AI & ML layer
│   │   │   ├── preprocessing.py        # Image cleanup & enhancement
│   │   │   ├── ocr_engine.py            # Tesseract + PaddleOCR
│   │   │   ├── layout_detection.py     # Table & structure detection
│   │   │   ├── vision_llm.py            # Vision LLM (Qwen / LLaVA)
│   │   │   ├── ner_extraction.py        # Vendor & entity detection
│   │   │   └── confidence_scoring.py   # Field-level confidence
│   │
│   │   ├── models/                    # Data models
│   │   │   ├── invoice.py              # Invoice schema
│   │   │   ├── user.py
│   │   │   └── audit.py
│   │
│   │   ├── database/
│   │   │   ├── postgres.py             # Metadata DB
│   │   │   ├── mongodb.py              # Extracted JSON
│   │   │   ├── redis.py                # Cache / queue
│   │   │   └── repositories/
│   │   │       ├── invoice_repo.py
│   │   │       └── user_repo.py
│   │
│   │   ├── utils/
│   │   │   ├── image_utils.py
│   │   │   ├── regex_utils.py
│   │   │   ├── gst_utils.py
│   │   │   ├── math_utils.py
│   │   │   └── date_utils.py
│   │
│   └── tests/
│       ├── test_ocr.py
│       ├── test_extraction.py
│       ├── test_validation.py
│       └── test_api.py
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   │
│   ├── src/
│   │   ├── App.jsx                    # Root component
│   │   ├── main.jsx                   # Entry point
│   │
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Upload.jsx
│   │   │   ├── Review.jsx              # Manual correction UI
│   │   │   └── History.jsx
│   │
│   │   ├── components/
│   │   │   ├── upload/
│   │   │   │   ├── UploadZone.jsx
│   │   │   │   └── FileList.jsx
│   │   │   ├── review/
│   │   │   │   ├── InvoicePreview.jsx
│   │   │   │   ├── EditableField.jsx
│   │   │   │   └── ConfidenceBadge.jsx
│   │   │   └── common/
│   │   │       ├── Button.jsx
│   │   │       ├── Input.jsx
│   │   │       └── Loader.jsx
│   │
│   │   ├── services/
│   │   │   ├── api.js                  # Axios setup
│   │   │   ├── invoiceService.js
│   │   │   └── authService.js
│   │
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │
│   │   ├── utils/
│   │   │   ├── formatters.js
│   │   │   └── validators.js
│   │
│   │   └── styles/
│   │       └── global.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── raw_invoices/                  # Uploaded files
│   ├── processed_images/              # Preprocessed images
│   └── extracted_json/                # Final outputs
│
├── ml-models/
│   ├── ocr/
│   ├── vision-llm/
│   └── ner/
│
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── docker-compose.yml
│
├── scripts/
│   ├── setup.sh
│   ├── train_models.py
│   └── migrate_data.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
│
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
|-frontend.py