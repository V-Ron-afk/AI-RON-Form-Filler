# AI Auto Form Filler — API Documentation

## Base URL

| Environment | URL |
|-------------|-----|
| Local (Docker) | `http://localhost/api` |
| Local (dev server) | `http://localhost:8000/api` |

Interactive Swagger UI: `http://localhost/api/docs`  
ReDoc: `http://localhost/api/redoc`

---

## Authentication

All endpoints except `/auth/register` and `/auth/login` require a Bearer token.

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. Register

**POST** `/auth/register`

```json
// Request
{
  "email": "maria@example.com",
  "password": "mypassword123",
  "full_name": "Maria Santos"
}

// Response 201
{
  "id": 1,
  "email": "maria@example.com",
  "full_name": "Maria Santos",
  "is_active": true,
  "created_at": "2025-04-15T08:00:00Z"
}
```

---

### 2. Login

**POST** `/auth/login`  
Content-Type: `application/x-www-form-urlencoded`

```
username=maria@example.com&password=mypassword123
```

```json
// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "maria@example.com",
    "full_name": "Maria Santos",
    "is_active": true,
    "created_at": "2025-04-15T08:00:00Z"
  }
}
```

---

### 3. Upload Document

**POST** `/documents/upload`  
Content-Type: `multipart/form-data`

```bash
curl -X POST http://localhost/api/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/your-document.pdf"
```

```json
// Response 201
{
  "id": 42,
  "filename": "passport_scan.pdf",
  "file_type": "pdf",
  "status": "completed",
  "extracted_data": { "fields": [...], "tables": [...] },
  "created_at": "2025-04-15T08:05:00Z",
  "processed_at": "2025-04-15T08:05:03Z"
}
```

---

### 4. Get Extraction Result

**GET** `/documents/{doc_id}/extraction`

Returns the full extraction enriched with:
- `form_values` — mapped to canonical field names, ready to populate the form
- `confidence_map` — per-field confidence scores (0.0–1.0) for UI highlighting
- `form_schema` — the dynamic form field definitions

```json
// Response 200
{
  "document_id": 42,
  "status": "completed",
  "model_used": "prebuilt-document",
  "raw_text_preview": "REPUBLIC OF THE PHILIPPINES...",
  "fields": [
    { "key": "full_name",     "value": "Maria Santos",     "confidence": 0.97, "page": 1 },
    { "key": "date_of_birth", "value": "1990-03-15",       "confidence": 0.95, "page": 1 },
    { "key": "id_number",     "value": "PSN-2024-00123",   "confidence": 0.99, "page": 1 },
    { "key": "email",         "value": "maria@example.com","confidence": 0.93, "page": 1 },
    { "key": "phone",         "value": "+63 917 123 4567", "confidence": 0.88, "page": 1 },
    { "key": "monthly_income","value": "85000",             "confidence": 0.65, "page": 2 }
  ],
  "tables": [
    [
      { "item": "Passport",       "number": "P1234567",   "expiry": "2030-01-01" },
      { "item": "Driver License", "number": "DL-9876543", "expiry": "2027-06-15" }
    ]
  ],
  "form_values": {
    "full_name":      "Maria Santos",
    "date_of_birth":  "1990-03-15",
    "email":          "maria@example.com",
    "phone":          "+63 917 123 4567",
    "address":        null,
    "id_number":      "PSN-2024-00123",
    "nationality":    null,
    "employer":       null,
    "position":       null,
    "monthly_income": "85000",
    "civil_status":   null
  },
  "confidence_map": {
    "full_name":      0.97,
    "date_of_birth":  0.95,
    "email":          0.93,
    "phone":          0.88,
    "id_number":      0.99,
    "monthly_income": 0.65
  },
  "form_schema": [
    { "name": "full_name",     "label": "Full Name",         "field_type": "text",   "required": true  },
    { "name": "date_of_birth", "label": "Date of Birth",     "field_type": "date",   "required": true  },
    { "name": "email",         "label": "Email Address",     "field_type": "email",  "required": true  },
    { "name": "phone",         "label": "Phone Number",      "field_type": "text",   "required": false },
    { "name": "address",       "label": "Home Address",      "field_type": "text",   "required": true  },
    { "name": "id_number",     "label": "ID / Passport No.", "field_type": "text",   "required": true  },
    { "name": "civil_status",  "label": "Civil Status",      "field_type": "select", "required": false,
      "options": ["Single", "Married", "Widowed", "Separated"] }
  ]
}
```

**Confidence score interpretation:**

| Score | Colour in UI | Meaning |
|-------|-------------|---------|
| ≥ 0.90 | 🟢 Green | High confidence — likely correct |
| 0.70–0.89 | 🟡 Amber | Medium — review before submitting |
| < 0.70 | 🔴 Red | Low — manual correction recommended |
| absent | ⚫ Grey | Field not found in document |

---

### 5. Submit Form

**POST** `/forms/submit`

User-edited form data. Call this after the user reviews and optionally edits the auto-filled values.

```json
// Request
{
  "document_id": 42,
  "label": "Maria's application - April 2025",
  "form_data": {
    "full_name":      "Maria Santos",
    "date_of_birth":  "1990-03-15",
    "email":          "maria@example.com",
    "phone":          "+63 917 123 4567",
    "address":        "123 Rizal St, Quezon City",
    "id_number":      "PSN-2024-00123",
    "nationality":    "Filipino",
    "employer":       "Acme Corp",
    "position":       "Software Engineer",
    "monthly_income": "85000",
    "civil_status":   "Single"
  }
}

// Response 201
{
  "id": 7,
  "document_id": 42,
  "form_data": { ... },
  "label": "Maria's application - April 2025",
  "created_at": "2025-04-15T08:10:00Z"
}
```

---

### 6. Export as JSON

**GET** `/export/{submission_id}/json`

```bash
curl -OJ http://localhost/api/export/7/json \
  -H "Authorization: Bearer <token>"
```

Downloads `submission_7.json`.

---

### 7. Export as PDF

**GET** `/export/{submission_id}/pdf`

```bash
curl -OJ http://localhost/api/export/7/pdf \
  -H "Authorization: Bearer <token>"
```

Downloads `submission_7.pdf` — a formatted A4 report.

---

### 8. List Documents

**GET** `/documents/?skip=0&limit=20`

```json
// Response 200
[
  {
    "id": 42,
    "filename": "passport_scan.pdf",
    "file_type": "pdf",
    "status": "completed",
    "created_at": "2025-04-15T08:05:00Z",
    "processed_at": "2025-04-15T08:05:03Z"
  }
]
```

---

### 9. List Submissions

**GET** `/forms/?skip=0&limit=20`

---

## Error Responses

All errors follow this shape:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Code | Meaning |
|-----------|---------|
| 400 | Bad request (validation error) |
| 401 | Missing or invalid JWT |
| 403 | Forbidden (wrong user) |
| 404 | Resource not found |
| 413 | File too large (> 20 MB) |
| 422 | Unprocessable entity |
| 500 | Server / Azure extraction error |

---

## Supported File Types

| Extension | MIME Type | Notes |
|-----------|-----------|-------|
| `.pdf` | `application/pdf` | Best for structured forms |
| `.jpg`, `.jpeg` | `image/jpeg` | Scanned images |
| `.png` | `image/png` | Screenshots, photos |
| `.tiff` | `image/tiff` | High-res scans |
| `.bmp` | `image/bmp` | Legacy scans |

Max file size: **20 MB**
