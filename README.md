# 🤖 AI Auto Form Filler

> Extract structured data from documents using **Google Document AI** (free tier) and auto-fill web forms — with editing, export, and history.

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 📄 Document Upload | PDF, JPG, PNG, TIFF, WebP — drag & drop or click |
| 🤖 AI Extraction | Google Document AI — Form Parser processor |
| 🆓 Free Tier | 1,000 pages/month — no credit card required |
| 🎯 Smart Mapping | 30+ field aliases mapped to canonical form fields |
| 🟢 Confidence Scores | Per-field colour-coded UI (green/amber/red/grey) |
| ✏️ Editable Form | Full edit-before-submit capability |
| 💾 Persistence | PostgreSQL — all documents & submissions saved |
| 📦 Export | Download as JSON or formatted PDF |
| 📜 History | Browse past documents & submissions |
| 🔐 JWT Auth | Secure register / login with bcrypt passwords |
| 🐳 Docker | One-command full-stack startup |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Angular 17)                 │
│  Upload → AI Review → Edit Form → Save → Export         │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP  /api/*
┌────────────────────▼────────────────────────────────────┐
│                  nginx (port 80)                         │
│  Static files  +  Reverse proxy → backend:8000          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              FastAPI (Python 3.12)                       │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Routes  │→ │ Google DocAI Svc │→ │ Google Cloud  │  │
│  │  (API)   │  │  (form_parser)   │  │  Document AI  │  │
│  └──────────┘  └──────────────────┘  └───────────────┘  │
│                ┌──────────────┐                         │
│                │  PostgreSQL  │                         │
│                └──────────────┘                         │
└─────────────────────────────────────────────────────────┘
```

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

## ☁️ Google Document AI Setup (Free Tier)

### Step 1 — Create a GCP project
1. Go to https://console.cloud.google.com/projectcreate
2. Give it any name, note the **Project Number** (an integer like `123456789012`)

### Step 2 — Enable the Document AI API
```
https://console.cloud.google.com/apis/library/documentai.googleapis.com
```
Click **Enable**.

### Step 3 — Create a Form Parser processor
1. Go to https://console.cloud.google.com/ai/document-ai/processors
2. Click **Create Processor**
3. Search for and select **Form Parser** (this is the free-tier processor)
4. Choose region `us` or `eu`, give it a name, click **Create**
5. Copy the **Processor ID** from the details page (e.g. `abc1234567890def`)

### Step 4 — Create a service-account key
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click **Create Service Account**
3. Name it anything (e.g. `formfiller-sa`), click **Create and Continue**
4. Grant the role **Document AI API User**, click **Done**
5. Click on the service account → **Keys** tab → **Add Key** → **JSON**
6. Save the downloaded file as `backend/credentials/gcp-service-account.json`

### Step 5 — Fill in `.env`

```env
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-service-account.json
GOOGLE_CLOUD_PROJECT_ID=123456789012        # your project NUMBER
GOOGLE_CLOUD_LOCATION=us
GOOGLE_DOCUMENTAI_PROCESSOR_ID=abc1234567890def
```

### Free tier limits

| Resource | Free quota |
|----------|-----------|
| Form Parser pages | 1,000 / month |
| Regions | us, eu |
| File types | PDF, JPEG, PNG, TIFF, BMP, GIF, WebP |
| Max file size | 20 MB (our backend limit) |

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

---

## 🧑‍💻 Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GCP values or leave blank for mock mode

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start   # http://localhost:4200
```

---

## 🔒 Security Notes

- GCP service-account JSON is **gitignored** — never commit it
- The `credentials/` directory is mounted **read-only** into Docker
- Passwords hashed with **bcrypt** (work factor 12)
- JWTs expire after **8 hours** (configurable)
- Each user can only access their own documents and submissions

---

## 🧩 Extending the System

### Add a new form field

1. `backend/app/services/form/mapping_service.py` → add to `FORM_SCHEMA`
2. Add Google DocAI entity type aliases to `FIELD_ALIASES`
3. Frontend re-renders dynamically — no Angular changes needed

### Switch to a specialised processor

Google Document AI offers specialised processors for higher accuracy:

| Processor | Best for | Free? |
|-----------|----------|-------|
| Form Parser | General forms | ✅ Yes |
| Document OCR | Raw text extraction | ✅ Yes |
| ID Document Parser | Passports, driver licenses | ⚠️ Paid |
| Invoice Parser | Invoices, receipts | ⚠️ Paid |

To switch: update `GOOGLE_DOCUMENTAI_PROCESSOR_ID` in `.env` — no code changes.

---

## 📄 License

MIT — free to use, modify, and deploy.
