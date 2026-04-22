"""
Google Document AI Service
============================
Two-stage extraction pipeline:

  Stage 1 — Google Document AI OCR
    Uses the FORM_PARSER processor for structured forms (extracts labeled
    key/value pairs directly).  If the document has no form fields (e.g. a
    resume, free-text letter, ID card), falls through to Stage 2.

  Stage 2 — Custom NLP parser
    Runs smart regex + heuristic parsing on the raw OCR text to extract:
      • Contact info  (name, email, phone, address, LinkedIn, GitHub)
      • Dates         (date of birth, issue/expiry dates)
      • Identity      (ID numbers, passport, SSS, TIN, PhilHealth, etc.)
      • Employment    (job titles, companies, dates)
      • Education     (degrees, schools, graduation years)
      • Skills        (programming languages, tools, frameworks)
    Works well on resumes, CVs, government IDs, and any unstructured doc.

KEY DESIGN: lazy client initialisation.
  - The Google SDK client is created on the FIRST upload call, never at import.
  - Missing credentials never crash startup.
  - Mock mode works with zero GCP config.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.core.config import settings
from app.schemas.schemas import ExtractedField, ExtractionResult

logger = logging.getLogger("ai_form_filler.google_docai")


# ── Custom NLP Parser ──────────────────────────────────────────────────────────

class DocumentParser:
    """
    Heuristic parser that extracts structured fields from raw OCR text.
    Handles resumes, CVs, government forms, IDs, and general documents.
    """

    EMAIL_RE    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)
    PHONE_RE    = re.compile(
        r"(?:\+?\d{1,3}[\s\-.]?)?"
        r"(?:\(?\d{2,4}\)?[\s\-.]?)?"
        r"\d{3,4}[\s\-.]?\d{3,4}"
    )
    LINKEDIN_RE = re.compile(r"linkedin\.com/in/([^\s/]+)", re.I)
    GITHUB_RE   = re.compile(r"github\.com/([^\s/]+)", re.I)
    LABEL_VALUE_RE = re.compile(r"^([A-Za-z][A-Za-z\s/]{2,30}?)\s*:\s*(.+)$", re.MULTILINE)

    JOB_TITLE_WORDS = {
        "engineer","developer","analyst","manager","director","officer",
        "coordinator","specialist","consultant","architect","designer",
        "administrator","supervisor","lead","head","chief","president",
        "vice","assistant","associate","intern","technician","programmer",
    }

    DEGREE_WORDS = {
        "bachelor","master","doctor","phd","mba","b.s.","m.s.","b.a.",
        "m.a.","b.sc","m.sc","b.e.","m.e.","bscs","bsit","bsece",
        "associate","diploma","certificate",
    }

    SKILL_KEYWORDS = {
        "python","java","javascript","typescript","react","angular","vue",
        "node","django","fastapi","flask","spring","sql","postgresql",
        "mysql","mongodb","redis","docker","kubernetes","aws","azure",
        "gcp","git","linux","html","css","c++","c#","php","ruby",
        "swift","kotlin","flutter","tensorflow","pytorch","excel","word",
        "powerpoint","photoshop","figma","jira","confluence",
    }

    def parse(self, raw_text: str) -> List[ExtractedField]:
        fields: List[ExtractedField] = []
        fields += self._extract_label_values(raw_text)
        fields += self._extract_contact(raw_text)
        fields += self._extract_name(raw_text)
        fields += self._extract_dates(raw_text)
        fields += self._extract_ids(raw_text)
        fields += self._extract_employment(raw_text)
        fields += self._extract_education(raw_text)
        fields += self._extract_skills(raw_text)

        seen: Dict[str, ExtractedField] = {}
        for f in fields:
            if f.key not in seen or f.confidence > seen[f.key].confidence:
                seen[f.key] = f
        return list(seen.values())

    def _extract_label_values(self, text: str) -> List[ExtractedField]:
        fields = []
        skip_keys = {"http","https","www","re","ref","page","fax"}
        for m in self.LABEL_VALUE_RE.finditer(text):
            raw_key = m.group(1).strip()
            raw_val = m.group(2).strip()
            if not raw_val or raw_key.lower() in skip_keys or len(raw_val) > 200:
                continue
            fields.append(ExtractedField(
                key=self._normalize_key(raw_key), value=raw_val, confidence=0.85, page=1
            ))
        return fields

    def _extract_contact(self, text: str) -> List[ExtractedField]:
        fields = []
        emails = self.EMAIL_RE.findall(text)
        if emails:
            fields.append(ExtractedField(key="email", value=emails[0], confidence=0.97, page=1))

        phones = [p.strip() for p in self.PHONE_RE.findall(text) if len(re.sub(r"\D","",p)) >= 7]
        if phones:
            fields.append(ExtractedField(key="phone", value=phones[0], confidence=0.90, page=1))

        li = self.LINKEDIN_RE.search(text)
        if li:
            fields.append(ExtractedField(key="linkedin", value=f"linkedin.com/in/{li.group(1)}", confidence=0.95, page=1))

        gh = self.GITHUB_RE.search(text)
        if gh:
            fields.append(ExtractedField(key="github", value=f"github.com/{gh.group(1)}", confidence=0.95, page=1))

        addr = self._find_address(text)
        if addr:
            fields.append(ExtractedField(key="address", value=addr, confidence=0.75, page=1))
        return fields

    def _extract_name(self, text: str) -> List[ExtractedField]:
        m = re.search(r"(?:full\s+)?name\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})", text, re.I)
        if m:
            return [ExtractedField(key="full_name", value=m.group(1).strip(), confidence=0.92, page=1)]
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$", line):
                if line.lower() not in {"curriculum vitae","resume","cv"}:
                    return [ExtractedField(key="full_name", value=line, confidence=0.80, page=1)]
            break
        return []

    def _extract_dates(self, text: str) -> List[ExtractedField]:
        fields = []
        dob = re.search(
            r"(?:date\s+of\s+birth|dob|birth\s*date)\s*[:\-]?\s*"
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            text, re.I)
        if dob:
            fields.append(ExtractedField(key="date_of_birth", value=dob.group(1).strip(), confidence=0.93, page=1))

        expiry = re.search(
            r"(?:expir(?:y|ation|es?)\s*(?:date)?|valid\s+until|valid\s+thru)\s*[:\-]?\s*"
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{4})", text, re.I)
        if expiry:
            fields.append(ExtractedField(key="expiry_date", value=expiry.group(1).strip(), confidence=0.88, page=1))

        nationality = re.search(r"(?:nationality|citizenship)\s*[:\-]?\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)", text, re.I)
        if nationality:
            fields.append(ExtractedField(key="nationality", value=nationality.group(1).strip(), confidence=0.85, page=1))
        return fields

    def _extract_ids(self, text: str) -> List[ExtractedField]:
        fields = []
        for pattern, key in [
            (r"passport\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z]{1,2}\d{6,8})", "passport_number"),
            (r"(?:sss\s*(?:no\.?|number|#)?|social\s+security)\s*[:\-]?\s*(\d{2}-\d{7}-\d)", "sss_number"),
            (r"(?:tin|tax\s+id)\s*(?:no\.?|number|#)?\s*[:\-]?\s*(\d{3}-\d{3}-\d{3}(?:-\d{3})?)", "tin_number"),
            (r"philhealth\s*(?:no\.?|number|#|id)?\s*[:\-]?\s*(\d{12}|\d{2}-\d{9}-\d)", "philhealth_number"),
            (r"(?:pag-?ibig|hdmf)\s*(?:no\.?|number|#|mid)?\s*[:\-]?\s*(\d{4}-\d{4}-\d{4}|\d{12})", "pagibig_number"),
        ]:
            m = re.search(pattern, text, re.I)
            if m:
                fields.append(ExtractedField(key=key, value=m.group(1), confidence=0.95, page=1))
        return fields

    def _extract_employment(self, text: str) -> List[ExtractedField]:
        fields = []
        m = re.search(r"(?:position|job\s+title|designation|role)\s*[:\-]?\s*(.+)", text, re.I)
        if m:
            fields.append(ExtractedField(key="job_title", value=m.group(1).strip()[:80], confidence=0.85, page=1))
        else:
            for line in text.splitlines():
                words = set(line.lower().split())
                if words & self.JOB_TITLE_WORDS and 1 <= len(words) <= 6:
                    fields.append(ExtractedField(key="job_title", value=line.strip(), confidence=0.65, page=1))
                    break

        m = re.search(r"(?:employer|company|organization|organisation|firm)\s*[:\-]?\s*(.+)", text, re.I)
        if m:
            fields.append(ExtractedField(key="employer", value=m.group(1).strip()[:100], confidence=0.82, page=1))

        m = re.search(
            r"(?:salary|compensation|income|rate)\s*[:\-]?\s*([\$\u20b1]?\s*[\d,]+(?:\.\d{2})?(?:\s*(?:per\s+(?:month|year)|monthly|annually))?)",
            text, re.I)
        if m:
            fields.append(ExtractedField(key="salary", value=m.group(1).strip(), confidence=0.80, page=1))
        return fields

    def _extract_education(self, text: str) -> List[ExtractedField]:
        fields = []
        m = re.search(r"(?:degree|qualification|course)\s*[:\-]?\s*(.+)", text, re.I)
        if m:
            fields.append(ExtractedField(key="degree", value=m.group(1).strip()[:100], confidence=0.82, page=1))
        else:
            for line in text.splitlines():
                if any(d in line.lower() for d in self.DEGREE_WORDS):
                    fields.append(ExtractedField(key="degree", value=line.strip()[:100], confidence=0.70, page=1))
                    break

        m = re.search(r"(?:university|college|institute|school|academy)\s+of\s+[A-Z][A-Za-z\s]+", text)
        if m:
            fields.append(ExtractedField(key="school", value=m.group(0).strip()[:120], confidence=0.78, page=1))

        m = re.search(r"(?:graduated?|graduation|class\s+of)\s*[:\-]?\s*(\d{4})", text, re.I)
        if m:
            fields.append(ExtractedField(key="graduation_year", value=m.group(1), confidence=0.85, page=1))
        return fields

    def _extract_skills(self, text: str) -> List[ExtractedField]:
        m = re.search(
            r"(?:technical\s+)?skills?\s*[:\-]\s*\n?([\s\S]{10,400}?)(?:\n\n|\Z|(?=\n[A-Z]{3,}))",
            text, re.I)
        if m:
            raw = re.sub(r"[•·▪▸\-\*]", ",", m.group(1))
            raw = re.sub(r"\s+", " ", raw).strip()
            return [ExtractedField(key="skills", value=raw[:300], confidence=0.80, page=1)]

        found = [s for s in self.SKILL_KEYWORDS if re.search(rf"\b{re.escape(s)}\b", text, re.I)]
        if found:
            return [ExtractedField(key="skills", value=", ".join(sorted(found)), confidence=0.60, page=1)]
        return []

    def _find_address(self, text: str) -> Optional[str]:
        indicators = ["street","st.","ave","avenue","blvd","road","rd.","barangay",
                      "brgy","city","province","floor","bldg","building","lot","block"]
        for line in text.splitlines():
            if any(i in line.lower() for i in indicators) and 10 < len(line.strip()) < 150:
                return line.strip()
        m = re.search(r"(?:address|location|residence)\s*[:\-]?\s*(.{10,120})", text, re.I)
        return m.group(1).strip() if m else None

    @staticmethod
    def _normalize_key(raw: str) -> str:
        s = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", raw)
        return s.lower().strip().rstrip(":").replace(" ","_").replace("-","_").replace("/","_").replace(".","_")


# ── Main Service ───────────────────────────────────────────────────────────────

class GoogleDocumentAIService:

    def __init__(self):
        self._client = None
        self._processor_name: Optional[str] = None
        self._parser = DocumentParser()

        creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS.strip()
        if creds_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip() == "":
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

        missing = [v for v in [
            "GOOGLE_CLOUD_PROJECT_ID","GOOGLE_CLOUD_LOCATION","GOOGLE_DOCUMENTAI_PROCESSOR_ID",
        ] if not getattr(settings, v, "").strip()]

        if missing:
            logger.warning(f"Google Document AI: missing config {missing}. MOCK mode active.")
            self._mock_mode = True
        else:
            self._mock_mode = False
            logger.info("Google Document AI configured (OCR + custom NLP parser).")

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google.cloud import documentai
        except ImportError:
            raise RuntimeError("google-cloud-documentai not installed")
        try:
            self._client = documentai.DocumentProcessorServiceClient()
            self._processor_name = self._client.processor_path(
                settings.GOOGLE_CLOUD_PROJECT_ID,
                settings.GOOGLE_CLOUD_LOCATION,
                settings.GOOGLE_DOCUMENTAI_PROCESSOR_ID,
            )
            logger.info(f"Google Document AI client ready: {self._processor_name}")
            return self._client
        except Exception as e:
            self._client = None
            raise RuntimeError(
                f"Google Document AI auth failed: {e}\n"
                "Run 'gcloud auth application-default login' then restart the container."
            ) from e

    async def analyze_document(self, file_path: str, file_content: bytes, content_type: str) -> ExtractionResult:
        if self._mock_mode:
            return self._mock_extraction(file_path)
        import asyncio
        logger.info(f"Sending to Google Document AI: {Path(file_path).name} ({len(file_content):,} bytes)")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_google_api, file_content, content_type)

    def _call_google_api(self, file_content: bytes, mime_type: str) -> ExtractionResult:
        from google.cloud import documentai
        from google.api_core.exceptions import GoogleAPICallError
        client = self._get_client()
        try:
            raw_doc = documentai.RawDocument(content=file_content, mime_type=mime_type)
            request = documentai.ProcessRequest(name=self._processor_name, raw_document=raw_doc)
            response = client.process_document(request=request)
            return self._parse_google_result(response.document)
        except GoogleAPICallError as e:
            logger.error(f"Google Document AI API error: {e}")
            raise RuntimeError(f"Extraction failed: {e}") from e

    def _parse_google_result(self, document: Any) -> ExtractionResult:
        raw_text = document.text or ""
        fields: List[ExtractedField] = []
        merged_tables: List[List[Dict[str, Any]]] = []

        # ── Stage 1a: Custom Extractor entities ───────────────────────────────
        # Custom Extractor processors return results as document.entities
        # (nested structure with parent + child properties)
        entity_fields_found = 0

        for entity in document.entities:
            parent_key = self._parser._normalize_key(entity.type_ or "")
            if not parent_key:
                continue

            # If entity has child properties (e.g. personal_information → full_name, email, etc.)
            if entity.properties:
                for prop in entity.properties:
                    child_key  = self._parser._normalize_key(prop.type_ or "")
                    # mention_text is the raw extracted text from the document
                    value_text = (prop.mention_text or "").strip()
                    if prop.normalized_value and prop.normalized_value.text:
                        value_text = prop.normalized_value.text.strip()
                    confidence = prop.confidence or 0.0
                    page_num   = (
                        prop.page_anchor.page_refs[0].page + 1
                        if prop.page_anchor and prop.page_anchor.page_refs else 1
                    )
                    key = child_key if child_key else f"{parent_key}_value"
                    # Include even empty values so user can see what was detected
                    fields.append(ExtractedField(
                        key=key,
                        value=value_text if value_text else None,
                        confidence=round(confidence, 4),
                        page=page_num,
                    ))
                    entity_fields_found += 1
            else:
                # Leaf entity (e.g. certifications, professional_summary, tools_and_technologies)
                value_text = (entity.mention_text or "").strip()
                if entity.normalized_value and entity.normalized_value.text:
                    value_text = entity.normalized_value.text.strip()
                confidence = entity.confidence or 0.0
                page_num   = (
                    entity.page_anchor.page_refs[0].page + 1
                    if entity.page_anchor and entity.page_anchor.page_refs else 1
                )
                fields.append(ExtractedField(
                    key=parent_key,
                    value=value_text if value_text else None,
                    confidence=round(confidence, 4),
                    page=page_num,
                ))
                entity_fields_found += 1

        logger.info(f"Custom Extractor entities parsed: {entity_fields_found} fields")

        # ── Stage 1b: Form Parser fields (fallback for form-type processors) ──
        form_fields_found = 0
        for page_num, page in enumerate(document.pages, start=1):
            for form_field in page.form_fields:
                key_text   = self._get_text(form_field.field_name,  raw_text).strip()
                value_text = self._get_text(form_field.field_value, raw_text).strip()
                if not key_text:
                    continue
                confidence = form_field.field_value.confidence if form_field.field_value else 0.0
                fields.append(ExtractedField(
                    key=self._parser._normalize_key(key_text),
                    value=value_text or None,
                    confidence=round(confidence, 4),
                    page=page_num,
                ))
                form_fields_found += 1

            # Tables
            for table in page.tables:
                header_cells = table.header_rows[0].cells if table.header_rows else []
                headers = [
                    self._get_text(cell.layout, raw_text).strip() or f"col_{i}"
                    for i, cell in enumerate(header_cells)
                ]
                rows = []
                for body_row in table.body_rows:
                    row = {
                        (headers[i] if i < len(headers) else f"col_{i}"):
                        self._get_text(cell.layout, raw_text).strip()
                        for i, cell in enumerate(body_row.cells)
                    }
                    if any(row.values()):
                        rows.append(row)
                if rows:
                    merged_tables.append(rows)

        structured_found = entity_fields_found + form_fields_found

        # ── Stage 2: Custom NLP parser (fills gaps or handles plain OCR docs) ─
        if raw_text.strip():
            nlp_fields = self._parser.parse(raw_text)
            if structured_found == 0:
                logger.info(f"No structured fields — NLP parser extracted {len(nlp_fields)} fields")
                fields = nlp_fields
            else:
                existing_keys = {f.key for f in fields}
                gap_fills = [f for f in nlp_fields if f.key not in existing_keys]
                logger.info(f"NLP gap-fill: added {len(gap_fills)} extra fields")
                fields += gap_fills

        # Deduplicate — keep highest confidence per key
        seen: Dict[str, ExtractedField] = {}
        for f in fields:
            if f.key not in seen or f.confidence > seen[f.key].confidence:
                seen[f.key] = f

        total = len(seen)
        logger.info(
            f"Extraction complete: {total} fields total "
            f"(entities={entity_fields_found}, form={form_fields_found}, nlp={total - structured_found})"
        )

        return ExtractionResult(
            document_id=0, status="completed",
            fields=list(seen.values()), tables=merged_tables,
            raw_text=raw_text[:3000] if raw_text else None,
            model_used="Google Document AI",
        )

    @staticmethod
    def _get_text(layout: Any, raw_text: str) -> str:
        if not layout or not layout.text_anchor:
            return ""
        result = ""
        for seg in layout.text_anchor.text_segments:
            start = int(seg.start_index) if seg.start_index else 0
            end   = int(seg.end_index)   if seg.end_index   else 0
            result += raw_text[start:end]
        return result

    @staticmethod
    def _mock_extraction(file_path: str) -> ExtractionResult:
        logger.info("MOCK MODE: returning sample extraction data")
        return ExtractionResult(
            document_id=0, status="completed",
            fields=[
                ExtractedField(key="full_name",       value="Maria Santos",                confidence=0.97, page=1),
                ExtractedField(key="email",           value="maria.santos@example.com",    confidence=0.93, page=1),
                ExtractedField(key="phone",           value="+63 917 123 4567",            confidence=0.88, page=1),
                ExtractedField(key="address",         value="123 Rizal St, Quezon City",   confidence=0.91, page=1),
                ExtractedField(key="linkedin",        value="linkedin.com/in/mariasantos", confidence=0.95, page=1),
                ExtractedField(key="job_title",       value="Software Engineer",           confidence=0.82, page=1),
                ExtractedField(key="employer",        value="Acme Corporation",            confidence=0.82, page=1),
                ExtractedField(key="skills",          value="Python, React, PostgreSQL, Docker", confidence=0.80, page=1),
                ExtractedField(key="degree",          value="BS Computer Science",         confidence=0.85, page=2),
                ExtractedField(key="school",          value="University of Santo Tomas",   confidence=0.78, page=2),
                ExtractedField(key="graduation_year", value="2018",                        confidence=0.85, page=2),
            ],
            tables=[],
            raw_text="[Mock — set GCP vars in .env for real extraction]",
            model_used="Google Document AI (Mock)",
        )


# Safe to import — __init__ never touches the Google SDK
google_docai_service = GoogleDocumentAIService()
