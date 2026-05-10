# 🤖 DocuFill AI  ·  Personal Project

> Extract structured data from documents using **Google Document AI**. Upload any document resume, government form, ID and let AI automatically extract and fill in all form fields for you.

---

## 🏗️ Architecture - The system uses a two-stage extraction pipeline powered by Google Document AI:

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER UPLOADS DOCUMENT                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              GOOGLE DOCUMENT AI  (OCR + Custom Extractor)       │
│                                                                 │
│   Processor: AI-resumeform (Custom Extractor)                   │
│   Model:     pretrained-foundation-model (auto-upgraded)        │
│                                                                 │
│   Extracts structured schema fields:                            │
│   ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐    │
│   │ personal_info   │  │ work_experience  │  │  education  │    │
│   │ ├ full_name     │  │ ├ job_title      │  │ ├ degree    │    │
│   │ ├ email_address │  │ ├ company        │  │ ├ school    │    │
│   │ ├ contact_number│  │ └ dates          │  │ └ grad_year │    │
│   │ ├ city          │  └──────────────────┘  └─────────────┘    │
│   │ └ country       │  ┌──────────────────┐  ┌─────────────┐    │
│   └─────────────────┘  │     skills       │  │   project   │    │
│                        │ ├ soft_skills    │  │ ├ proj_name │    │
│                        │ ├ technical      │  │ ├ desc      │    │
│                        │ └ tools          │  │ └ tech_used │    │
│                        └──────────────────┘  └─────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
               ┌─────────────┴──────────────┐
               │                            │
               ▼                            ▼
   ┌───────────────────────┐   ┌────────────────────────────┐
   │  Structured fields    │   │  No fields found           │
   │  found (forms, IDs)   │   │  (free-text documents)     │
   │                       │   │                            │
   │  Stage 1 results used │   │  Falls through to Stage 2  │
   └───────────┬───────────┘   └────────────┬───────────────┘
               │                            │
               │                            ▼
               │               ┌────────────────────────────┐
               │               │   STAGE 2: CUSTOM NLP      │
               │               │   PARSER (regex + heuristic│
               │               │                            │
               │               │  Extracts from raw OCR:    │
               │               │  • Name (first-line + label│
               │               │  • Email, Phone, LinkedIn  │
               │               │  • Address (street keywords│
               │               │  • DOB, expiry dates       │
               │               │  • SSS, TIN, PhilHealth    │
               │               │  • Passport, Pag-IBIG      │
               │               │  • Job title, Employer     │
               │               │  • Degree, School          │
               │               │  • Skills (section + scan) │
               └───────────────┴────────────────────────────┘
                             │
                             │  Gap-fill: NLP adds any fields
                             │  missed by the form parser
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MERGED RESULT                               │
│         Deduplicated · Highest confidence wins                  │
│         Mapped to frontend form fields                          │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               USER REVIEWS & EDITS IN BROWSER                   │
│           Confidence badges: 🟢 High  🟡 Medium  🔴 Low        
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXPORT  (PDF or JSON)                        │
│               Saved to per-user submission history              │
└─────────────────────────────────────────────────────────────────┘
```
## 🛠️ Tech Stack
 
### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.12 | Runtime |
| **FastAPI** | 0.111 | REST API framework |
| **Uvicorn** | 0.29 | ASGI server |
| **SQLAlchemy** | 2.0 | Async ORM |
| **asyncpg** | 0.29 | Async PostgreSQL driver |
| **Pydantic v2** | 2.7 | Data validation & settings |
| **python-jose** | 3.3 | JWT token generation |
| **passlib + bcrypt** | 1.7 / 4.0 | Password hashing |
| **ReportLab** | 4.1 | PDF export generation |
| **google-cloud-documentai** | 2.29 | Google Document AI SDK |
| **google-auth** | 2.29 | GCP Application Default Credentials |
 
### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **Angular** | 17 | SPA framework |
| **TypeScript** | 5.4 | Language |
| **Tailwind CSS** | 3.4 | Utility-first styling |
| **RxJS** | 7.8 | Reactive data streams |
| **nginx** | 1.25 | Production static file server + API proxy |
 
### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Containerization & orchestration |
| **PostgreSQL 16** | Persistent data store |
| **Google Document AI** | OCR + Custom Extractor AI processor |
| **Google Cloud ADC** | Credential management (no service account key files) |
---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- (Optional) Google Cloud account for real extraction

### 1. Clone & configure

```bash
git clone <repo-url>
cd ai-form-filler
cp backend/.env.example backend/.env
```

### 2. Start without GCP (Mock mode — no account needed)

Leave the Google fields blank in `backend/.env` — the app returns
realistic sample data so you can test the entire UI flow.

```bash
docker compose up --build
```

### 3. Start with real Google Document AI extraction

Follow the **GCP Setup** section below, then:

```bash
# Put your downloaded service-account JSON here:
mkdir -p backend/credentials
cp ~/Downloads/my-key.json backend/credentials/gcp-service-account.json

# Fill in backend/.env:
# GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-service-account.json
# GOOGLE_CLOUD_PROJECT_ID=123456789012
# GOOGLE_CLOUD_LOCATION=us
# GOOGLE_DOCUMENTAI_PROCESSOR_ID=abc1234567890def

docker compose up --build
```

| Service | URL |
|---------|-----|
| **App** | http://localhost |
| **API Docs** | http://localhost/api/docs |
| **Backend** | http://localhost:8000 |

---

## 📁 Project Structure

```
ai-form-filler/
├── backend/
│   ├── credentials/                       ← Put GCP service-account JSON here
│   │   └── .gitkeep                       ← Directory is tracked, key is gitignored
│   ├── app/
│   │   ├── main.py
│   │   ├── core/config.py                 ← Google DocAI settings via env vars
│   │   ├── services/ai/
│   │   │   └── google_docai_service.py    ← Google Document AI integration
│   │   ├── services/form/
│   │   │   └── mapping_service.py         ← 30+ field aliases (incl. DocAI entity types)
│   │   └── services/export/
│   │       └── export_service.py          ← JSON + PDF export (ReportLab)
│   ├── requirements.txt                   ← google-cloud-documentai >= 2.20
│   ├── Dockerfile
│   └── .env.example
├── frontend/                              ← Angular 17 + Tailwind CSS (unchanged)
├── docker-compose.yml                     ← credentials/ volume mount added
└── README.md
```



