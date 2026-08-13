import sys
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[2] / "backend"))

from app.main import app
from app.schemas.features import (
    FeatureMeasurement,
    PredictionRequest,
    PredictionResponse,
)
from app.services.feature_dictionary import validate_basic_features
from app.services.prediction_service import PredictionService
from app.services.report_parser import parse_report_pages, parse_report_text


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_measurements():
    return [
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


def test_prediction_schema_rejects_invalid_probability() -> None:
    with pytest.raises(ValidationError):
        PredictionResponse(
            prediction_available=True,
            prediction_status="demo",
            risk_probability=1.5,
            risk_level="HIGH",
            model_version="demo-v0",
            features_used=["age"],
            influential_features=[],
            warnings=[],
            disclaimer="Research prototype only.",
            missing_required_features=[],
        )


def test_valid_prediction_request_returns_demo_prediction(valid_measurements) -> None:
    request = PredictionRequest(measurements=valid_measurements)
    result = PredictionService().predict(request.measurements)
    assert result.prediction_available is True
    assert result.prediction_status in {"demo", "model"}
    assert 0.0 <= result.risk_probability <= 1.0
    assert result.risk_level in {"LOW", "MODERATE", "HIGH"}


def test_parse_report_text_recognizes_age_and_gender_without_mapping_unrelated_labs() -> None:
    parsed = parse_report_text(
        "Age: 46 Years\nGender: Female\nESR: 28 mm/hr\nCRP: 8.7 mg/L\nUric Acid: 6.2 mg/dL\nRheumatoid Factor: 31 IU/mL"
    )

    names = {feature.canonical_name for feature in parsed.features}
    assert "age" in names
    assert "sex" in names
    assert "esr" in names
    assert "crp" in names
    assert "uric_acid" in names
    assert "bmi" not in names
    assert "hba1c" not in names
    assert "fasting_glucose" not in names
    assert "ldl" not in names


def test_parse_report_text_handles_realistic_pdf_style_variants() -> None:
    parsed = parse_report_text(
        "Age 45 years\nSex: Female\nFasting Glucose 98 mg/dL\nHbA1c 5.4 %\nTotal Cholesterol 170 mg/dL\nHDL 52 mg/dL\nLDL 90 mg/dL\nTriglycerides 110 mg/dL\nCreatinine 0.9 mg/dL"
    )

    names = {feature.canonical_name for feature in parsed.features}
    assert "age" in names
    assert "sex" in names
    assert "fasting_glucose" in names
    assert "hba1c" in names
    assert "total_cholesterol" in names
    assert "hdl" in names
    assert "ldl" in names
    assert "triglycerides" in names
    assert "creatinine" in names


def test_parse_report_text_handles_tabbed_and_whitespace_fragmentation() -> None:
    parsed = parse_report_text("Age\t46\nGender\tFemale\nBMI\t23.4 kg/m2\nFBS\t96\tmg/dL")

    names = {feature.canonical_name for feature in parsed.features}
    assert "age" in names
    assert "sex" in names
    assert "bmi" in names
    assert "fasting_glucose" in names


def test_pdf_validate_route_extracts_age_and_gender_from_generated_pdf(client, tmp_path) -> None:
    pdf_path = tmp_path / "lab_report.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Age: 45 years\nGender: Female\nFBS: 98 mg/dL\nHbA1c: 5.4 %\nTotal Cholesterol: 170 mg/dL\nHDL: 52 mg/dL\nLDL: 90 mg/dL\nTriglycerides: 110 mg/dL\nCreatinine: 0.9 mg/dL",
    )
    document.save(pdf_path)
    document.close()

    response = client.post("/reports/pdf/validate", files={"file": ("lab_report.pdf", pdf_path.read_bytes(), "application/pdf")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["extraction_success"] is True
    assert payload["extracted_features"]
    assert payload["validation"]["eligible_for_basic_model"] is True
    assert payload["validation"]["missing_required_features"] == []


def test_parser_scans_entire_document_and_detects_later_page_demographics() -> None:
    pages = [
        {"page_number": 1, "text": "Lab summary\nESR 22 mm/hr\nCRP 5.6 mg/L"},
        {"page_number": 2, "text": "Age 46 years\nGender: Female"},
    ]

    parsed = parse_report_pages(pages)
    names = {feature.canonical_name for feature in parsed.features}
    assert "age" in names
    assert "sex" in names
    assert "esr" in names
    assert "crp" in names


def test_parser_detects_required_features_across_multiple_pages() -> None:
    pages = [
        {"page_number": 1, "text": "Fasting Glucose 98 mg/dL\nHDL 52 mg/dL"},
        {"page_number": 2, "text": "Creatinine 0.9 mg/dL\nTotal Cholesterol 170 mg/dL"},
        {"page_number": 3, "text": "Age 45 years\nSex Female\nTriglycerides 110 mg/dL\nLDL 90 mg/dL\nHbA1c 5.4 %"},
    ]

    parsed = parse_report_pages(pages)
    names = {feature.canonical_name for feature in parsed.features}
    assert {"age", "sex", "fasting_glucose", "hba1c", "total_cholesterol", "hdl", "ldl", "triglycerides", "creatinine"}.issubset(names)


def test_parser_keeps_source_page_for_each_detected_feature() -> None:
    pages = [
        {"page_number": 1, "text": "Uric Acid 6.2 mg/dL"},
        {"page_number": 2, "text": "Age 46 years\nSex: Female"},
        {"page_number": 3, "text": "FBS 96 mg/dL\nBMI 23.5 kg/m2"},
    ]

    parsed = parse_report_pages(pages)
    by_name = {feature.canonical_name: feature.source_page for feature in parsed.features}
    assert by_name["age"] == 2
    assert by_name["sex"] == 2
    assert by_name["fasting_glucose"] == 3
    assert by_name["bmi"] == 3


def test_parser_ignores_unrelated_lab_parameters_across_pages() -> None:
    pages = [
        {"page_number": 1, "text": "ESR 28 mm/hr\nCRP 8.7 mg/L"},
        {"page_number": 2, "text": "Rheumatoid Factor 32 IU/mL\nUric Acid 6.1 mg/dL"},
        {"page_number": 3, "text": "Age 47 years\nGender Male"},
    ]

    parsed = parse_report_pages(pages)
    names = {feature.canonical_name for feature in parsed.features}
    assert "age" in names
    assert "sex" in names
    assert "esr" in names
    assert "crp" in names
    assert "uric_acid" in names
    assert "bmi" not in names
    assert "fasting_glucose" not in names
    assert "hba1c" not in names
    assert "ldl" not in names


def test_pdf_validate_route_scans_all_pages_and_reports_source_pages(client, tmp_path) -> None:
    pdf_path = tmp_path / "multi_page_lab.pdf"
    document = fitz.open()
    first = document.new_page()
    first.insert_text((72, 72), "ESR 28 mm/hr\nCRP 8.7 mg/L")
    second = document.new_page()
    second.insert_text((72, 72), "Age 46 years\nGender: Female")
    third = document.new_page()
    third.insert_text((72, 72), "FBS 96 mg/dL\nHDL 52 mg/dL\nLDL 90 mg/dL\nTriglycerides 110 mg/dL\nCreatinine 0.9 mg/dL")
    document.save(pdf_path)
    document.close()

    response = client.post("/reports/pdf/validate", files={"file": ("multi_page_lab.pdf", pdf_path.read_bytes(), "application/pdf")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["page_count"] == 3
    assert payload["extraction_success"] is True
    assert len(payload["extracted_features"]) >= 8
    detected_pages = {item["source_page"] for item in payload["extracted_features"]}
    assert detected_pages == {1, 2, 3}
    assert any(item["canonical_name"] == "age" for item in payload["extracted_features"])
    assert any(item["canonical_name"] == "sex" for item in payload["extracted_features"])
    assert payload["validation"]["eligible_for_basic_model"] is False
    assert payload["validation"]["missing_required_features"]


def test_incomplete_prediction_request_returns_unavailable() -> None:
    request = PredictionRequest(
        measurements=[
            FeatureMeasurement(name="age", value="42", unit="years"),
            FeatureMeasurement(name="gender", value="female"),
        ]
    )
    result = PredictionService().predict(request.measurements)
    assert result.prediction_available is False
    assert result.prediction_status == "unavailable"
    assert result.missing_required_features


def test_unavailable_prediction_keeps_detected_demographics_and_missing_requirements() -> None:
    result = PredictionService().predict(
        [
            FeatureMeasurement(name="age", value="46", unit="years"),
            FeatureMeasurement(name="gender", value="female"),
            FeatureMeasurement(name="esr", value="28", unit="mm/hr"),
            FeatureMeasurement(name="crp", value="8.7", unit="mg/L"),
            FeatureMeasurement(name="uric acid", value="6.2", unit="mg/dL"),
        ]
    )

    assert result.prediction_available is False
    assert result.prediction_status == "unavailable"
    assert {"age", "sex"}.issubset(set(result.features_used))
    assert result.missing_required_features
    assert any("Missing required features" in warning for warning in result.warnings)


def test_invalid_feature_is_rejected() -> None:
    request = PredictionRequest(
        measurements=[
            FeatureMeasurement(name="age", value="42", unit="years"),
            FeatureMeasurement(name="gender", value="female"),
            FeatureMeasurement(name="bmi", value="23.5", unit="kg/m2"),
            FeatureMeasurement(name="notareal", value="99", unit="mg/dL"),
        ]
    )
    validation = validate_basic_features(request.measurements)
    assert any(item.name == "notareal" for item in validation.invalid_features)


def test_risk_probability_bounds(valid_measurements) -> None:
    result = PredictionService().predict(valid_measurements)
    assert 0.0 <= result.risk_probability <= 1.0


def test_risk_level_generation() -> None:
    assert PredictionService().risk_level_for_probability(0.10) == "LOW"
    assert PredictionService().risk_level_for_probability(0.55) == "MODERATE"
    assert PredictionService().risk_level_for_probability(0.85) == "HIGH"


def test_model_loading_handles_missing_artifact() -> None:
    service = PredictionService(model_path="models/artifacts/definitely_missing_model.json")
    assert service.model is None
    assert service.model_status == "demo"


def test_pdf_prediction_route(client, tmp_path) -> None:
    pdf_path = tmp_path / "report.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Age: 42 years\nGender: female\nBMI: 23.5 kg/m2\nFBS: 96 mg/dL\nHbA1c: 5.4 %\nTotal Cholesterol: 170 mg/dL\nHDL: 52 mg/dL\nLDL: 90 mg/dL\nTriglycerides: 110 mg/dL\nCreatinine: 0.9 mg/dL",
    )
    document.save(pdf_path)
    document.close()

    response = client.post("/reports/pdf/predict", files={"file": ("report.pdf", pdf_path.read_bytes(), "application/pdf")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction_available"] in {True, False}
    assert payload["prediction_status"] in {"demo", "model", "unavailable"}


def test_missing_feature_prediction_route(client) -> None:
    response = client.post(
        "/reports/predict",
        json={"measurements": [{"name": "age", "value": "42", "unit": "years"}, {"name": "gender", "value": "female"}]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction_available"] is False
    assert payload["prediction_status"] == "unavailable"
    assert payload["missing_required_features"]


def test_shap_response_uses_model_influential_features(valid_measurements) -> None:
    result = PredictionService().predict(valid_measurements)
    assert hasattr(result, "influential_features")
    assert isinstance(result.influential_features, list)


def test_model_unavailable_state_returns_honest_warning() -> None:
    service = PredictionService(model_path="models/artifacts/definitely_missing_model.json")
    result = service.predict([
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
    ])
    assert result.prediction_status == "demo"
    assert "demo" in result.warnings[0].lower()


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
