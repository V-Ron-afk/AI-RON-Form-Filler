"""
Unit tests for core AI and mapping logic.
Run with: pytest app/tests/ -v
"""

import pytest
from app.schemas.schemas import ExtractedField
from app.services.form.mapping_service import map_fields_to_form, get_confidence_map, FORM_SCHEMA


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_fields():
    """Realistic extraction output from Azure."""
    return [
        ExtractedField(key="full_name",      value="Maria Santos",     confidence=0.97, page=1),
        ExtractedField(key="dob",            value="1990-03-15",       confidence=0.95, page=1),
        ExtractedField(key="email_address",  value="maria@example.com",confidence=0.93, page=1),
        ExtractedField(key="mobile_number",  value="+63 917 123 4567", confidence=0.88, page=1),
        ExtractedField(key="home_address",   value="123 Rizal St",     confidence=0.91, page=1),
        ExtractedField(key="id_no",          value="PSN-2024-00123",   confidence=0.99, page=1),
        ExtractedField(key="monthly_income", value="85000",            confidence=0.65, page=2),
    ]


# ── Field Mapping Tests ────────────────────────────────────────────────────────

class TestFieldMapping:

    def test_canonical_fields_mapped(self, sample_fields):
        result = map_fields_to_form(sample_fields)
        assert result["full_name"] == "Maria Santos"
        assert result["date_of_birth"] == "1990-03-15"   # alias: dob
        assert result["email"] == "maria@example.com"    # alias: email_address
        assert result["phone"] == "+63 917 123 4567"     # alias: mobile_number
        assert result["address"] == "123 Rizal St"       # alias: home_address
        assert result["id_number"] == "PSN-2024-00123"   # alias: id_no

    def test_missing_fields_return_none(self, sample_fields):
        result = map_fields_to_form(sample_fields)
        assert result["nationality"] is None
        assert result["employer"] is None

    def test_all_schema_fields_present(self, sample_fields):
        result = map_fields_to_form(sample_fields)
        schema_names = {f.name for f in FORM_SCHEMA}
        assert schema_names == set(result.keys())

    def test_highest_confidence_wins(self):
        """When same canonical field appears twice, keep highest confidence."""
        fields = [
            ExtractedField(key="full_name", value="Wrong",  confidence=0.5,  page=1),
            ExtractedField(key="full_name", value="Correct", confidence=0.97, page=1),
        ]
        result = map_fields_to_form(fields)
        assert result["full_name"] == "Correct"

    def test_empty_fields_list(self):
        result = map_fields_to_form([])
        assert all(v is None for v in result.values())


class TestConfidenceMap:

    def test_confidence_map_uses_canonical_names(self, sample_fields):
        confidence = get_confidence_map(sample_fields)
        # dob alias should map to date_of_birth
        assert "date_of_birth" in confidence
        assert confidence["date_of_birth"] == pytest.approx(0.95)

    def test_confidence_range(self, sample_fields):
        confidence = get_confidence_map(sample_fields)
        for score in confidence.values():
            assert 0.0 <= score <= 1.0
