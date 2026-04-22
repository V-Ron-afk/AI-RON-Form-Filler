"""
Form Mapping Service
=====================
Maps raw AI-extracted fields → the target form schema.

Why this exists:
  The AI returns keys like "date_of_birth" or "dob" or "birth date" —
  all meaning the same thing. This service normalises them to the
  canonical form-field names your frontend expects.

You can extend FIELD_MAP to support custom document types.
"""

from typing import Dict, List, Optional
from app.schemas.schemas import ExtractedField, FormFieldDef

# ── Canonical form fields ─────────────────────────────────────────────────────
# These are the fields rendered in the frontend form.
FORM_SCHEMA: List[FormFieldDef] = [
    FormFieldDef(name="full_name",      label="Full Name",          field_type="text",   required=True),
    FormFieldDef(name="date_of_birth",  label="Date of Birth",      field_type="date",   required=True),
    FormFieldDef(name="email",          label="Email Address",      field_type="email",  required=True),
    FormFieldDef(name="phone",          label="Phone Number",       field_type="text",   required=False),
    FormFieldDef(name="address",        label="Home Address",       field_type="text",   required=True),
    FormFieldDef(name="id_number",      label="ID / Passport No.",  field_type="text",   required=True),
    FormFieldDef(name="nationality",    label="Nationality",        field_type="text",   required=False),
    FormFieldDef(name="employer",       label="Employer / Company", field_type="text",   required=False),
    FormFieldDef(name="position",       label="Job Title",          field_type="text",   required=False),
    FormFieldDef(name="monthly_income", label="Monthly Income",     field_type="number", required=False),
    FormFieldDef(
        name="civil_status", label="Civil Status", field_type="select", required=False,
        options=["Single", "Married", "Widowed", "Separated"]
    ),
]

# ── Alias map — all known synonyms → canonical name ──────────────────────────
# Covers both Google Document AI entity types AND common form-field label text.
# Add more aliases as you encounter new document layouts.
FIELD_ALIASES: Dict[str, str] = {
    # ── Names ─────────────────────────────────────────────────────────────
    "name":                   "full_name",
    "full name":              "full_name",
    "applicant_name":         "full_name",
    "first_last_name":        "full_name",
    # Google DocAI entity types
    "receiver_name":          "full_name",
    "given_names":            "full_name",
    "family_name":            "full_name",

    # ── Dates ─────────────────────────────────────────────────────────────
    "dob":                    "date_of_birth",
    "birth_date":             "date_of_birth",
    "birthdate":              "date_of_birth",
    "date_of_birth":          "date_of_birth",
    # Google DocAI entity types
    "date":                   "date_of_birth",

    # ── Contact ───────────────────────────────────────────────────────────
    "email_address":          "email",
    "mobile":                 "phone",
    "mobile_number":          "phone",
    "telephone":              "phone",
    "contact_number":         "phone",
    # Google DocAI entity types
    "phone_number":           "phone",

    # ── Address ───────────────────────────────────────────────────────────
    "home_address":           "address",
    "residential_address":    "address",
    "street_address":         "address",
    # Google DocAI entity types
    "receiver_address":       "address",

    # ── IDs ───────────────────────────────────────────────────────────────
    "passport_number":        "id_number",
    "id_no":                  "id_number",
    "government_id":          "id_number",
    "tin":                    "id_number",
    # Google DocAI entity types
    "document_id":            "id_number",
    "id":                     "id_number",

    # ── Employment ────────────────────────────────────────────────────────
    "company":                "employer",
    "company_name":           "employer",
    "job_title":              "position",
    "occupation":             "position",
    "designation":            "position",
    "salary":                 "monthly_income",
    "income":                 "monthly_income",
    # Google DocAI entity types
    "net_amount":             "monthly_income",
    "total_amount":           "monthly_income",

    # ── Civil status ──────────────────────────────────────────────────────
    "marital_status":         "civil_status",
    "status":                 "civil_status",
}


def map_fields_to_form(
    extracted_fields: List[ExtractedField],
) -> Dict[str, Optional[str]]:
    """
    Converts a list of raw ExtractedField objects into a dict keyed
    by the canonical form-field name.

    Steps:
    1. Try exact match on canonical name
    2. Try alias lookup
    3. Fall back to None (field stays empty for user to fill)
    """
    # Build lookup: canonical_name → best ExtractedField (highest confidence)
    canonical: Dict[str, ExtractedField] = {}

    for field in extracted_fields:
        key = field.key.strip().lower()

        # Direct canonical match
        canon = key if any(f.name == key for f in FORM_SCHEMA) else None

        # Alias lookup
        if canon is None:
            canon = FIELD_ALIASES.get(key)

        if canon and (
            canon not in canonical
            or field.confidence > canonical[canon].confidence
        ):
            canonical[canon] = field

    # Build final mapping
    form_values: Dict[str, Optional[str]] = {}
    for form_field in FORM_SCHEMA:
        matched = canonical.get(form_field.name)
        form_values[form_field.name] = matched.value if matched else None

    return form_values


def get_confidence_map(extracted_fields: List[ExtractedField]) -> Dict[str, float]:
    """Return confidence scores per canonical field name (for UI highlighting)."""
    confidence: Dict[str, float] = {}
    for field in extracted_fields:
        key = field.key.strip().lower()
        canon = key if any(f.name == key for f in FORM_SCHEMA) else FIELD_ALIASES.get(key)
        if canon:
            confidence[canon] = max(confidence.get(canon, 0.0), field.confidence)
    return confidence
