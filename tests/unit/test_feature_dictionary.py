import sys
from decimal import Decimal
from pathlib import Path

import fitz
import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[2] / "backend"))

from app.schemas.features import FeatureMeasurement
from app.services.feature_dictionary import validate_basic_features
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.report_parser import parse_report_pages


def basic_measurements() -> list[FeatureMeasurement]:
    return [
        FeatureMeasurement(name="Age", value=Decimal(42), unit="years"),
        FeatureMeasurement(name="Gender", value="female"),
        FeatureMeasurement(name="BMI", value=Decimal("23.5"), unit="kg/m2"),
        FeatureMeasurement(name="FBS", value=Decimal(96), unit="mg/dL"),
        FeatureMeasurement(name="HbA1c", value=Decimal("5.4"), unit="%"),
        FeatureMeasurement(name="Total Cholesterol", value=Decimal(170), unit="mg/dL"),
        FeatureMeasurement(name="HDL", value=Decimal(52), unit="mg/dL"),
        FeatureMeasurement(name="LDL", value=Decimal(90), unit="mg/dL"),
        FeatureMeasurement(name="Triglycerides", value=Decimal(110), unit="mg/dL"),
        FeatureMeasurement(name="Creatinine", value=Decimal("0.9"), unit="mg/dL"),
    ]


def test_complete_basic_input_is_eligible() -> None:
    result = validate_basic_features(basic_measurements())

    assert result.eligible_for_basic_model is True
    assert result.missing_required_features == []
    assert result.invalid_features == []


def test_missing_basic_input_returns_safe_fallback() -> None:
    measurements = [item for item in basic_measurements() if item.name.lower() != "creatinine"]
    result = validate_basic_features(measurements)

    assert result.eligible_for_basic_model is False
    assert result.missing_required_features == ["creatinine"]
    assert "Prediction unavailable" in result.message


def test_bmi_is_derived_only_from_explicit_height_and_weight() -> None:
    measurements = [item for item in basic_measurements() if item.name.lower() != "bmi"]
    measurements.extend(
        [
            FeatureMeasurement(name="Height", value=Decimal(170), unit="cm"),
            FeatureMeasurement(name="Weight", value=Decimal(70), unit="kg"),
        ]
    )

    result = validate_basic_features(measurements)

    assert result.eligible_for_basic_model is True
    assert result.derived_features == ["bmi"]


def test_alias_normalization_works() -> None:
    result = validate_basic_features(
        [
            FeatureMeasurement(name="Age", value=Decimal(45), unit="years"),
            FeatureMeasurement(name="Sex", value="female"),
            FeatureMeasurement(name="Hb", value=Decimal("14.0"), unit="g/dL"),
            FeatureMeasurement(name="FBS", value=Decimal(98), unit="mg/dL"),
            FeatureMeasurement(name="HbA1c", value=Decimal("5.6"), unit="%"),
            FeatureMeasurement(name="Total Cholesterol", value=Decimal(180), unit="mg/dL"),
            FeatureMeasurement(name="HDL", value=Decimal(48), unit="mg/dL"),
            FeatureMeasurement(name="LDL", value=Decimal(102), unit="mg/dL"),
            FeatureMeasurement(name="Triglycerides", value=Decimal(130), unit="mg/dL"),
            FeatureMeasurement(name="Creatinine", value=Decimal("1.0"), unit="mg/dL"),
            FeatureMeasurement(name="BMI", value=Decimal("24.1"), unit="kg/m2"),
        ]
    )

    assert result.eligible_for_basic_model is True
    assert "hemoglobin" in {feat.canonical_name for feat in result.normalized_features}


def test_unsupported_feature_is_rejected() -> None:
    result = validate_basic_features(
        [
            FeatureMeasurement(name="Age", value=Decimal(45), unit="years"),
            FeatureMeasurement(name="Gender", value="female"),
            FeatureMeasurement(name="BMI", value=Decimal(25), unit="kg/m2"),
            FeatureMeasurement(name="FBS", value=Decimal(98), unit="mg/dL"),
            FeatureMeasurement(name="HbA1c", value=Decimal("5.5"), unit="%"),
            FeatureMeasurement(name="Total Cholesterol", value=Decimal(180), unit="mg/dL"),
            FeatureMeasurement(name="HDL", value=Decimal(50), unit="mg/dL"),
            FeatureMeasurement(name="LDL", value=Decimal(110), unit="mg/dL"),
            FeatureMeasurement(name="Triglycerides", value=Decimal(140), unit="mg/dL"),
            FeatureMeasurement(name="Creatinine", value=Decimal("1.0"), unit="mg/dL"),
            FeatureMeasurement(name="NotARealFeature", value=Decimal(99), unit="mg/dL"),
        ]
    )

    assert any(item.name == "notarealfeature" for item in result.invalid_features)


def test_unsupported_unit_is_rejected() -> None:
    result = validate_basic_features(
        [
            FeatureMeasurement(name="Age", value=Decimal(50), unit="years"),
            FeatureMeasurement(name="Gender", value="female"),
            FeatureMeasurement(name="BMI", value=Decimal(26), unit="kg/m2"),
            FeatureMeasurement(name="FBS", value=Decimal(100), unit="mmol/L"),
            FeatureMeasurement(name="HbA1c", value=Decimal("5.4"), unit="%"),
            FeatureMeasurement(name="Total Cholesterol", value=Decimal(170), unit="mg/dL"),
            FeatureMeasurement(name="HDL", value=Decimal(50), unit="mg/dL"),
            FeatureMeasurement(name="LDL", value=Decimal(100), unit="mg/dL"),
            FeatureMeasurement(name="Triglycerides", value=Decimal(130), unit="mg/dL"),
            FeatureMeasurement(name="Creatinine", value=Decimal("1.0"), unit="mg/dL"),
        ]
    )

    assert any("Unsupported unit" in item.reason for item in result.invalid_features)


def test_duplicate_feature_is_reported() -> None:
    result = validate_basic_features(
        [
            FeatureMeasurement(name="Age", value=Decimal(44), unit="years"),
            FeatureMeasurement(name="Gender", value="female"),
            FeatureMeasurement(name="BMI", value=Decimal("23.8"), unit="kg/m2"),
            FeatureMeasurement(name="FBS", value=Decimal(93), unit="mg/dL"),
            FeatureMeasurement(name="HbA1c", value=Decimal("5.4"), unit="%"),
            FeatureMeasurement(name="Total Cholesterol", value=Decimal(160), unit="mg/dL"),
            FeatureMeasurement(name="HDL", value=Decimal(45), unit="mg/dL"),
            FeatureMeasurement(name="LDL", value=Decimal(92), unit="mg/dL"),
            FeatureMeasurement(name="Triglycerides", value=Decimal(95), unit="mg/dL"),
            FeatureMeasurement(name="Creatinine", value=Decimal("0.9"), unit="mg/dL"),
            FeatureMeasurement(name="Creatinine", value=Decimal("1.0"), unit="mg/dL"),
        ]
    )

    assert any("Duplicate" in item.reason for item in result.invalid_features)


def test_invalid_numeric_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FeatureMeasurement(name="Age", value=Decimal("NaN"), unit="years")

    valid_result = validate_basic_features(
        [
            FeatureMeasurement(name="Age", value=Decimal(42), unit="years"),
            FeatureMeasurement(name="Gender", value="female"),
            FeatureMeasurement(name="BMI", value=Decimal("24.5"), unit="kg/m2"),
            FeatureMeasurement(name="FBS", value=Decimal(96), unit="mg/dL"),
            FeatureMeasurement(name="HbA1c", value=Decimal("5.4"), unit="%"),
            FeatureMeasurement(name="Total Cholesterol", value=Decimal(170), unit="mg/dL"),
            FeatureMeasurement(name="HDL", value=Decimal(52), unit="mg/dL"),
            FeatureMeasurement(name="LDL", value=Decimal(90), unit="mg/dL"),
            FeatureMeasurement(name="Triglycerides", value=Decimal(110), unit="mg/dL"),
            FeatureMeasurement(name="Creatinine", value=Decimal("0.9"), unit="mg/dL"),
        ]
    )

    assert valid_result.eligible_for_basic_model is True


def test_numeric_strings_in_api_payloads_are_coerced() -> None:
    result = validate_basic_features(
        [
            FeatureMeasurement(name="age", value="42", unit="years"),
            FeatureMeasurement(name="gender", value="female"),
            FeatureMeasurement(name="bmi", value="23.5", unit="kg/m2"),
            FeatureMeasurement(name="fbs", value="96", unit="mg/dL"),
            FeatureMeasurement(name="hba1c", value="5.4", unit="%"),
            FeatureMeasurement(name="total cholesterol", value="170", unit="mg/dL"),
            FeatureMeasurement(name="hdl", value="52", unit="mg/dL"),
            FeatureMeasurement(name="ldl", value="90", unit="mg/dL"),
            FeatureMeasurement(name="triglycerides", value="110", unit="mg/dL"),
            FeatureMeasurement(name="creatinine", value="0.9", unit="mg/dL"),
        ]
    )

    assert result.eligible_for_basic_model is True
    assert result.invalid_features == []


def test_valid_text_pdf_page_count_and_text_are_preserved(tmp_path: Path) -> None:
    pdf_path = tmp_path / "report.pdf"
    document = fitz.open()
    first_page = document.new_page()
    first_page.insert_text((72, 72), "Age: 42 years\nGender: female")
    second_page = document.new_page()
    second_page.insert_text((72, 72), "FBS: 96 mg/dL\nHbA1c: 5.4 %")
    document.save(pdf_path)
    document.close()

    extraction = extract_text_from_pdf(pdf_path)

    assert extraction.extraction_success is True
    assert extraction.page_count == 2
    assert len(extraction.pages) == 2
    assert extraction.pages[0].page_number == 1
    assert extraction.pages[1].page_number == 2
    assert "Age: 42 years" in extraction.pages[0].text
    assert "FBS: 96 mg/dL" in extraction.pages[1].text


def test_invalid_pdf_is_reported(tmp_path: Path) -> None:
    pdf_path = tmp_path / "broken.pdf"
    pdf_path.write_bytes(b"not a valid pdf")

    extraction = extract_text_from_pdf(pdf_path)

    assert extraction.extraction_success is False
    assert extraction.page_count == 0
    assert extraction.extraction_method == "none"
    assert len(extraction.warnings) >= 1


def test_blank_pdf_warns_for_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    extraction = extract_text_from_pdf(pdf_path)

    assert extraction.extraction_success is True
    assert extraction.page_count == 1
    assert any("OCR" in warning or "selectable text" in warning for warning in extraction.warnings)


def test_parse_report_pages_keeps_source_pages() -> None:
    pages = [
        {"page_number": 1, "text": "Hemoglobin: 14 g/dL\nGender: female"},
        {"page_number": 2, "text": "FBS: 96 mg/dL\nHbA1c: 5.4 %\nCreatinine: 0.9 mg/dL"},
    ]

    result = parse_report_pages(pages)

    assert {feature.source_page for feature in result.features} == {1, 2}
    assert any(feature.canonical_name == "hemoglobin" for feature in result.features)
    assert any(feature.canonical_name == "hba1c" for feature in result.features)


def test_patient_demographics_on_multiple_pages_are_deduplicated() -> None:
    pages = [
        {"page_number": 1, "text": "Patient Age: 45 years\nSex: Female"},
        {"page_number": 2, "text": "Age/Gender: 45 years / Female"},
    ]

    result = parse_report_pages(pages)
    age_features = [feature for feature in result.features if feature.canonical_name == "age"]
    sex_features = [feature for feature in result.features if feature.canonical_name == "sex"]

    assert len(age_features) == 1
    assert len(sex_features) == 1
    assert all("Conflicting values detected" not in warning for warning in result.warnings)


def test_ocr_pipeline_tracks_every_page_and_uses_page_provenance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "report.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Age: 45 years")
    document.new_page().insert_text((72, 72), "Fasting Glucose 98 mg/dL")
    document.save(pdf_path)
    document.close()

    def fake_ocr(file_path: Path) -> list[dict[str, object]]:
        assert file_path == pdf_path
        return [
            {"page_number": 1, "text": "Patient Age: 45 years\nSex: Female"},
            {"page_number": 2, "text": "Fasting Glucose 98 mg/dL\nTotal Cholesterol 180 mg/dL"},
        ]

    monkeypatch.setattr("app.services.pdf_extractor._run_ocr_for_pdf", fake_ocr)

    result = extract_text_from_pdf(pdf_path)

    assert result.extraction_method == "ocr"
    assert result.page_count == 2
    assert [page.page_number for page in result.pages] == [1, 2]
    assert "Patient Age: 45 years" in result.pages[0].text
    assert "Fasting Glucose 98 mg/dL" in result.pages[1].text


def test_feature_discovery_aggregates_across_arbitrary_pages() -> None:
    pages = [
        {"page_number": 1, "text": "Patient Age: 45 years"},
        {"page_number": 4, "text": "LDL Cholesterol 120 mg/dL\nCreatinine 1.0 mg/dL"},
        {"page_number": 7, "text": "HbA1c 5.6 %"},
    ]

    result = parse_report_pages(pages, extraction_method="ocr")
    canonical_names = {feature.canonical_name for feature in result.features}

    assert "age" in canonical_names
    assert "ldl" in canonical_names
    assert "creatinine" in canonical_names
    assert "hba1c" in canonical_names
    assert {feature.source_page for feature in result.features} == {1, 4, 7}


def test_unrelated_numeric_values_are_ignored_without_context() -> None:
    pages = [
        {"page_number": 1, "text": "Invoice total: 473.20\nRoom number 7"},
        {"page_number": 2, "text": "Aspirin 300 mg\nTemperature 98.6 F"},
    ]

    result = parse_report_pages(pages, extraction_method="ocr")

    assert result.features == []
    assert any("No configured health parameters were recognized" in warning for warning in result.warnings)


def test_conflicting_values_are_reported_without_silent_overwrite() -> None:
    pages = [
        {"page_number": 1, "text": "Age: 45 years"},
        {"page_number": 2, "text": "Age: 47 years"},
    ]

    result = parse_report_pages(pages, extraction_method="ocr")

    assert len([feature for feature in result.features if feature.canonical_name == "age"]) == 2
    assert any("Conflicting values detected for 'age' on pages 1, 2" in warning for warning in result.warnings)


def test_reference_text_containing_age_is_ignored() -> None:
    pages = [{"page_number": 1, "text": "Reference range: Age 20-40 years\nTarget range for fasting glucose: 70-100 mg/dL"}]

    result = parse_report_pages(pages)
    age_matches = [feature for feature in result.features if feature.canonical_name == "age"]
    glucose_matches = [feature for feature in result.features if feature.canonical_name == "fasting_glucose"]

    assert age_matches == []
    assert glucose_matches == []


def test_laboratory_features_across_pages_are_aggregated() -> None:
    pages = [
        {"page_number": 1, "text": "Patient Age: 46 years\nSex: Female"},
        {"page_number": 2, "text": "Fasting Glucose 98 mg/dL"},
        {"page_number": 3, "text": "HbA1c 5.7 %\nLDL Cholesterol 110 mg/dL"},
    ]

    result = parse_report_pages(pages)
    aggregated = {feature.canonical_name: feature.value for feature in result.features}

    assert aggregated["age"] == Decimal(46)
    assert aggregated["sex"] == "female"
    assert aggregated["fasting_glucose"] == Decimal(98)
    assert aggregated["hba1c"] == Decimal("5.7")
    assert aggregated["ldl"] == Decimal(110)


def test_duplicate_laboratory_results_are_deduplicated() -> None:
    pages = [
        {"page_number": 1, "text": "Fasting Glucose 98 mg/dL"},
        {"page_number": 2, "text": "FBS: 98 mg/dL"},
    ]

    result = parse_report_pages(pages)
    fasting_glucose = [feature for feature in result.features if feature.canonical_name == "fasting_glucose"]

    assert len(fasting_glucose) == 1
    assert fasting_glucose[0].value == Decimal(98)
    assert all("Conflicting values detected" not in warning for warning in result.warnings)


def test_genuine_conflict_generates_warning() -> None:
    pages = [
        {"page_number": 1, "text": "Age: 45 years\nSex: Female"},
        {"page_number": 2, "text": "Patient Age: 46 years\nGender: Female"},
    ]

    result = parse_report_pages(pages)
    age_conflicts = [warning for warning in result.warnings if "age" in warning.lower()]

    assert age_conflicts


def test_missing_feature_remains_missing_after_validation() -> None:
    measurements = [
        FeatureMeasurement(name="Age", value=Decimal(45), unit="years"),
        FeatureMeasurement(name="Sex", value="female"),
        FeatureMeasurement(name="BMI", value=Decimal("24.0"), unit="kg/m2"),
        FeatureMeasurement(name="FBS", value=Decimal(96), unit="mg/dL"),
        FeatureMeasurement(name="HbA1c", value=Decimal("5.4"), unit="%"),
        FeatureMeasurement(name="Total Cholesterol", value=Decimal(170), unit="mg/dL"),
        FeatureMeasurement(name="HDL", value=Decimal(52), unit="mg/dL"),
        FeatureMeasurement(name="LDL", value=Decimal(90), unit="mg/dL"),
        FeatureMeasurement(name="Triglycerides", value=Decimal(110), unit="mg/dL"),
    ]

    result = validate_basic_features(measurements)
    assert result.missing_required_features == ["creatinine"]


def test_explanatory_text_containing_feature_names_is_ignored() -> None:
    pages = [{
        "page_number": 1,
        "text": "The Hba1c test measures glycated hemoglobin. Triglycerides are often discussed in educational material. Reference range for LDL is below 130 mg/dL.",
    }]

    result = parse_report_pages(pages)
    assert [feature.canonical_name for feature in result.features] == []


def test_parser_handles_adjacent_lines_value_split() -> None:
    pages = [
        {"page_number": 1, "text": "Fasting Glucose\n98 mg/dL"},
        {"page_number": 2, "text": "Age\n45 years"},
    ]

    result = parse_report_pages(pages, extraction_method="ocr")
    names = {feature.canonical_name for feature in result.features}
    assert "fasting_glucose" in names
    assert "age" in names
    
    glucose_feature = next(f for f in result.features if f.canonical_name == "fasting_glucose")
    assert glucose_feature.value == Decimal(98)
    assert glucose_feature.unit == "mg/dL"


def test_parser_deduplicates_identical_values_across_pages() -> None:
    pages = [
        {"page_number": 1, "text": "FBS: 98 mg/dL"},
        {"page_number": 2, "text": "Fasting Glucose 98 mg/dL"},
    ]

    result = parse_report_pages(pages, extraction_method="ocr")
    glucose_features = [f for f in result.features if f.canonical_name == "fasting_glucose"]
    assert len(glucose_features) == 1
    assert glucose_features[0].source_page == 1
    assert all("Conflicting values" not in warning for warning in result.warnings)


def test_validation_rejects_conflicting_values_as_invalid() -> None:
    measurements = [
        FeatureMeasurement(name="age", value=Decimal(45), unit="years", source="ocr", source_page=1),
        FeatureMeasurement(name="age", value=Decimal(47), unit="years", source="ocr", source_page=2),
    ]

    result = validate_basic_features(measurements)
    assert "age" not in result.available_features
    assert "age" in result.missing_required_features
    assert result.eligible_for_basic_model is False
    
    invalid_ages = [i for i in result.invalid_features if i.canonical_name == "age"]
    assert len(invalid_ages) == 2
    assert all(i.reason == "Duplicate/conflicting feature supplied." for i in invalid_ages)


def test_ocr_whitespaces_and_table_layouts() -> None:
    pages = [
        {"page_number": 1, "text": "Fasting  Glucose     98      mg/dL"},
        {"page_number": 1, "text": "Hb   A1c      5.4       %"},
    ]

    result = parse_report_pages(pages, extraction_method="ocr")
    names = {feature.canonical_name for feature in result.features}
    assert "fasting_glucose" in names
    assert "hba1c" in names


def test_nine_required_features_without_bmi_is_eligible() -> None:
    nine_features = [
        FeatureMeasurement(name="Age", value=Decimal(41), unit="years"),
        FeatureMeasurement(name="Sex", value="male"),
        FeatureMeasurement(name="Fasting Glucose", value=Decimal(85), unit="mg/dL"),
        FeatureMeasurement(name="HbA1c", value=Decimal("4.7"), unit="%"),
        FeatureMeasurement(name="Total Cholesterol", value=Decimal(184), unit="mg/dL"),
        FeatureMeasurement(name="HDL", value=Decimal(36), unit="mg/dL"),
        FeatureMeasurement(name="LDL", value=Decimal(133), unit="mg/dL"),
        FeatureMeasurement(name="Triglycerides", value=Decimal(74), unit="mg/dL"),
        FeatureMeasurement(name="Creatinine", value=Decimal("0.87"), unit="mg/dL"),
    ]
    result = validate_basic_features(nine_features)
    assert result.eligible_for_basic_model is True
    assert result.missing_required_features == []
    assert "bmi" not in result.missing_required_features
    assert "age" in result.available_features
    assert "creatinine" in result.available_features


def test_bmi_is_treated_as_optional_when_present() -> None:
    ten_features = [
        FeatureMeasurement(name="Age", value=Decimal(41), unit="years"),
        FeatureMeasurement(name="Sex", value="male"),
        FeatureMeasurement(name="Fasting Glucose", value=Decimal(85), unit="mg/dL"),
        FeatureMeasurement(name="HbA1c", value=Decimal("4.7"), unit="%"),
        FeatureMeasurement(name="Total Cholesterol", value=Decimal(184), unit="mg/dL"),
        FeatureMeasurement(name="HDL", value=Decimal(36), unit="mg/dL"),
        FeatureMeasurement(name="LDL", value=Decimal(133), unit="mg/dL"),
        FeatureMeasurement(name="Triglycerides", value=Decimal(74), unit="mg/dL"),
        FeatureMeasurement(name="Creatinine", value=Decimal("0.87"), unit="mg/dL"),
        FeatureMeasurement(name="BMI", value=Decimal("24.5"), unit="kg/m2"),
    ]
    result = validate_basic_features(ten_features)
    assert result.eligible_for_basic_model is True
    assert "bmi" in result.available_features
    assert result.missing_required_features == []


def test_age_gender_compound_header_and_value_extraction() -> None:
    pages = [
        {"page_number": 1, "text": "Age/Gender: 41 Y/Male"},
        {"page_number": 2, "text": "Age / Sex : 35 Yrs / Female"},
        {"page_number": 3, "text": "Age/Gender: 28/F"},
    ]
    # Page 1
    r1 = parse_report_pages([pages[0]], extraction_method="ocr")
    names1 = {f.canonical_name: f.value for f in r1.features}
    assert names1["age"] == Decimal(41)
    assert names1["sex"] == "male"

    # Page 2
    r2 = parse_report_pages([pages[1]], extraction_method="ocr")
    names2 = {f.canonical_name: f.value for f in r2.features}
    assert names2["age"] == Decimal(35)
    assert names2["sex"] == "female"

    # Page 3
    r3 = parse_report_pages([pages[2]], extraction_method="ocr")
    names3 = {f.canonical_name: f.value for f in r3.features}
    assert names3["age"] == Decimal(28)
    assert names3["sex"] == "female"


def test_fasting_glucose_naming_variants() -> None:
    variants = [
        "Glucose - Fasting Blood 85 mg/dL 70-105 Hexokinase/G-6-PDH",
        "Glucose - Fasting 90 mg/dL",
        "Fasting Blood Sugar 95 mg/dL",
        "FBS 92 mg/dL",
        "Fasting Glucose 88 mg/dL",
    ]
    for text in variants:
        res = parse_report_pages([{"page_number": 1, "text": text}], extraction_method="ocr")
        glucose = [f for f in res.features if f.canonical_name == "fasting_glucose"]
        assert len(glucose) == 1, f"Failed for variant: {text}"
        assert glucose[0].unit == "mg/dL"


def test_hba1c_parenthetical_format_and_unit() -> None:
    texts = [
        "Glycosylated Hemoglobin (HbA1c) 4.7 % 4-6 HPLC - Cation Exchange",
        "HbA1c (Glycated Hemoglobin) 5.8 %",
        "Hemoglobin A1c 6.1 %",
    ]
    for text in texts:
        res = parse_report_pages([{"page_number": 1, "text": text}], extraction_method="ocr")
        hba1c = [f for f in res.features if f.canonical_name == "hba1c"]
        assert len(hba1c) == 1, f"Failed for variant: {text}"
        assert hba1c[0].unit == "%"


def test_non_hdl_does_not_match_hdl() -> None:
    page = {
        "page_number": 9,
        "text": "HDL Cholesterol 36 mg/dL\nNon-HDL Cholesterol 148.00 mg/dl\nHDL/LDL Ratio 0.27 Ratio",
    }
    res = parse_report_pages([page], extraction_method="ocr")
    hdl_features = [f for f in res.features if f.canonical_name == "hdl"]
    assert len(hdl_features) == 1
    assert hdl_features[0].value == Decimal(36)
    assert hdl_features[0].unit == "mg/dL"


def test_vldl_does_not_match_ldl() -> None:
    page = {
        "page_number": 9,
        "text": "LDL Cholesterol 133 mg/dl\nVLDL Cholesterol 15 mg/dl\nLDL/HDL Ratio 3.70 Ratio",
    }
    res = parse_report_pages([page], extraction_method="ocr")
    ldl_features = [f for f in res.features if f.canonical_name == "ldl"]
    assert len(ldl_features) == 1
    assert ldl_features[0].value == Decimal(133)
    assert ldl_features[0].unit == "mg/dL"


def test_ratio_reference_and_educational_text_are_ignored() -> None:
    lines = [
        "Cholesterol : HDL Cholesterol 5.1 Ratio Calculated",
        "SGOT/SGPT 0.50 Ratio Calculated",
        "BUN/Creatinine Ratio 13.9 Ratio Calculated",
        "Condition _ mg/g Creatinine 0 = 300",
        "Inadequate dietary Vitamin D 3. Severe disease",
        "Deficiency:< 20",
    ]
    page = {"page_number": 1, "text": "\n".join(lines)}
    res = parse_report_pages([page], extraction_method="ocr")
    # None of these spurious lines should match
    assert len(res.features) == 0


def test_features_collected_from_different_pages() -> None:
    pages = [
        {"page_number": 1, "text": "Age/Gender: 41 Y/Male"},
        {"page_number": 6, "text": "Glucose - Fasting Blood 85 mg/dL"},
        {"page_number": 7, "text": "Glycosylated Hemoglobin (HbA1c) 4.7 %"},
        {"page_number": 9, "text": "Cholesterol 184 mg/dl\nHDL Cholesterol 36 mg/dL\nLDL Cholesterol 133 mg/dl\nTriglycerides 74 mg/dl"},
        {"page_number": 11, "text": "Creatinine 0.87 mg/dl"},
    ]
    res = parse_report_pages(pages, extraction_method="ocr")
    measurements = [FeatureMeasurement(name=f.canonical_name, value=f.value, unit=f.unit, source=f.source, source_page=f.source_page) for f in res.features]
    val = validate_basic_features(measurements)
    assert val.eligible_for_basic_model is True
    assert len(val.available_features) == 9
    assert val.missing_required_features == []

