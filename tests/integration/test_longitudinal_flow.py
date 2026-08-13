"""Integration tests for longitudinal patient-report analysis workflow."""

import io

import fitz
import pytest
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def in_memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(in_memory_db):
    return TestClient(app)


def _generate_synthetic_pdf(text_content: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text_content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_first_report_creates_baseline_without_deterioration(client) -> None:
    """Tests 1, 2, 16: First report creates a baseline, has no deterioration analysis or scores."""
    pdf_text = (
        "Age: 45 years\n"
        "Gender: Female\n"
        "Glucose - Fasting Blood: 95 mg/dL\n"
        "Glycosylated Hemoglobin (HbA1c): 5.2 %\n"
        "Total Cholesterol: 180 mg/dL\n"
        "HDL Cholesterol: 50 mg/dL\n"
        "LDL Cholesterol: 110 mg/dL\n"
        "Triglycerides: 100 mg/dL\n"
        "Creatinine: 0.85 mg/dL\n"
        "Calcium: 9.2 mg/dL\n"
        "Alanine Transaminase (SGPT): 28 U/L\n"
    )
    pdf_bytes = _generate_synthetic_pdf(pdf_text)

    response = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "patient-101", "report_series_name": "Annual Panel"},
        files={"file": ("report1.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_baseline"] is True
    assert "Baseline established" in data["message"]
    assert data["user_id"] == "patient-101"
    assert data["report_series_name"] == "Annual Panel"
    assert data["validation"]["eligible_for_basic_model"] is True
    assert data["feature_comparisons"] == []
    assert data["trajectory_summary"] is None
    assert data["previous_report_id"] is None
    # Verify no fake deterioration score / prediction is attached
    assert "risk_probability" not in data
    assert "deterioration_score" not in data


def test_second_report_for_same_user_and_series_performs_longitudinal_comparison(client) -> None:
    """Tests 3, 4, 7, 8: Second report finds previous report, compares against it, persists extra features."""
    # First report
    pdf1 = _generate_synthetic_pdf(
        "Age: 45 years\n"
        "Gender: Female\n"
        "Glucose - Fasting Blood: 90 mg/dL\n"
        "Glycosylated Hemoglobin (HbA1c): 5.0 %\n"
        "Total Cholesterol: 180 mg/dL\n"
        "HDL Cholesterol: 50 mg/dL\n"
        "LDL Cholesterol: 110 mg/dL\n"
        "Triglycerides: 100 mg/dL\n"
        "Creatinine: 0.80 mg/dL\n"
        "Alanine Transaminase (SGPT): 25 U/L\n"
    )
    res1 = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "patient-202", "report_series_name": "Checkup"},
        files={"file": ("r1.pdf", io.BytesIO(pdf1), "application/pdf")},
    )
    assert res1.status_code == 200
    report1_id = res1.json()["report_id"]

    # Second report: fasting glucose increased (90 -> 105), cholesterol decreased (180 -> 160), ALT persisted
    pdf2 = _generate_synthetic_pdf(
        "Age: 46 years\n"
        "Gender: Female\n"
        "Glucose - Fasting Blood: 105 mg/dL\n"
        "Glycosylated Hemoglobin (HbA1c): 5.4 %\n"
        "Total Cholesterol: 160 mg/dL\n"
        "HDL Cholesterol: 50 mg/dL\n"
        "LDL Cholesterol: 100 mg/dL\n"
        "Triglycerides: 95 mg/dL\n"
        "Creatinine: 0.80 mg/dL\n"
        "Alanine Transaminase (SGPT): 30 U/L\n"
    )
    res2 = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "patient-202", "report_series_name": "Checkup"},
        files={"file": ("r2.pdf", io.BytesIO(pdf2), "application/pdf")},
    )
    assert res2.status_code == 200
    data2 = res2.json()

    assert data2["is_baseline"] is False
    assert data2["previous_report_id"] == report1_id
    assert data2["trajectory_summary"] is not None
    assert len(data2["feature_comparisons"]) >= 9

    # Verify glucose increase
    glu = next(c for c in data2["feature_comparisons"] if c["canonical_name"] == "fasting_glucose")
    assert glu["previous_value"] == "90"
    assert glu["current_value"] == "105"
    assert glu["direction"] == "increased"
    assert glu["absolute_change"] == "15"

    # Verify cholesterol decrease
    chol = next(c for c in data2["feature_comparisons"] if c["canonical_name"] == "total_cholesterol")
    assert chol["previous_value"] == "180"
    assert chol["current_value"] == "160"
    assert chol["direction"] == "decreased"

    # Verify optional ALT is preserved and compared
    alt = next(c for c in data2["feature_comparisons"] if c["canonical_name"] == "alt")
    assert alt["previous_value"] == "25"
    assert alt["current_value"] == "30"
    assert alt["direction"] == "increased"


def test_user_and_series_isolation(client) -> None:
    """Tests 5, 6: Different users and different report series do not mix histories."""
    pdf_user_a_panel1 = _generate_synthetic_pdf(
        "Age: 40 years\nGender: Male\nGlucose - Fasting Blood: 90 mg/dL\nGlycosylated Hemoglobin (HbA1c): 5.1 %\n"
        "Total Cholesterol: 170 mg/dL\nHDL Cholesterol: 45 mg/dL\nLDL Cholesterol: 100 mg/dL\n"
        "Triglycerides: 110 mg/dL\nCreatinine: 0.9 mg/dL"
    )

    # 1. User A in "Annual Checkup" -> Baseline
    r_a1 = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "user-A", "report_series_name": "Annual Checkup"},
        files={"file": ("a1.pdf", io.BytesIO(pdf_user_a_panel1), "application/pdf")},
    )
    assert r_a1.json()["is_baseline"] is True

    # 2. User A in different series "Diabetes Panel" -> ALSO Baseline (does not mix series)
    r_a_diab = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "user-A", "report_series_name": "Diabetes Panel"},
        files={"file": ("a_diab.pdf", io.BytesIO(pdf_user_a_panel1), "application/pdf")},
    )
    assert r_a_diab.json()["is_baseline"] is True
    assert r_a_diab.json()["previous_report_id"] is None

    # 3. User B in "Annual Checkup" -> ALSO Baseline (does not mix users)
    r_b1 = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "user-B", "report_series_name": "Annual Checkup"},
        files={"file": ("b1.pdf", io.BytesIO(pdf_user_a_panel1), "application/pdf")},
    )
    assert r_b1.json()["is_baseline"] is True
    assert r_b1.json()["previous_report_id"] is None


def test_missing_required_feature_prevents_basic_model_eligibility(client) -> None:
    """Test 9: Missing one of 9 required features sets eligible_for_basic_model=False."""
    # Report missing creatinine and total_cholesterol
    pdf_incomplete = _generate_synthetic_pdf(
        "Age: 50 years\nGender: Female\nGlucose - Fasting Blood: 95 mg/dL\n"
        "Glycosylated Hemoglobin (HbA1c): 5.3 %\nHDL Cholesterol: 50 mg/dL\nLDL Cholesterol: 105 mg/dL"
    )
    res = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "patient-incomplete", "report_series_name": "General"},
        files={"file": ("inc.pdf", io.BytesIO(pdf_incomplete), "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["validation"]["eligible_for_basic_model"] is False
    assert "creatinine" in data["validation"]["missing_required_features"]
    assert "total_cholesterol" in data["validation"]["missing_required_features"]
    assert data["report_id"] is not None  # Report is still persisted


def test_no_fake_prediction_or_shap_when_no_xgboost_artifact(client) -> None:
    """Tests 17, 18: No fake prediction or SHAP values are fabricated when model artifact is absent."""
    pdf = _generate_synthetic_pdf(
        "Age: 45 years\nGender: Female\nGlucose - Fasting Blood: 95 mg/dL\n"
        "Glycosylated Hemoglobin (HbA1c): 5.2 %\nTotal Cholesterol: 180 mg/dL\n"
        "HDL Cholesterol: 50 mg/dL\nLDL Cholesterol: 110 mg/dL\nTriglycerides: 100 mg/dL\nCreatinine: 0.85 mg/dL"
    )
    # The analyze route returns pure longitudinal facts without fake predictions
    res = client.post(
        "/reports/pdf/analyze",
        data={"user_id": "patient-safe", "report_series_name": "General"},
        files={"file": ("safe.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "risk_probability" not in data
    assert "influential_features" not in data

    # The existing /reports/pdf/predict route explicitly returns demo status with honest warnings
    res_predict = client.post(
        "/reports/pdf/predict",
        files={"file": ("safe.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert res_predict.status_code == 200
    pred_data = res_predict.json()
    assert pred_data["prediction_status"] == "demo"
    assert pred_data["model_version"] == "demo-v0"
    assert pred_data["influential_features"] == []
    assert any("Demo mode is active" in w for w in pred_data["warnings"])
    assert any("SHAP explanation is unavailable" in w for w in pred_data["warnings"])
