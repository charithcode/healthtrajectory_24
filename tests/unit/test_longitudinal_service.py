"""Unit tests for the longitudinal comparison service."""

from decimal import Decimal

from app.schemas.features import ExtractedFeature
from app.services.longitudinal_service import compare_features


def _make_feat(canonical_name: str, value: str | Decimal, unit: str | None = "mg/dL") -> ExtractedFeature:
    return ExtractedFeature(
        name=canonical_name,
        canonical_name=canonical_name,
        value=Decimal(str(value)) if str(value).replace(".", "", 1).isdigit() else str(value),
        unit=unit,
        source="ocr",
        source_page=1,
        source_text=f"{canonical_name} {value} {unit or ''}".strip(),
        extraction_method="ocr",
    )


def test_feature_increase_calculated_correctly() -> None:
    """Test 10: Feature increases are calculated correctly."""
    prev = [_make_feat("fasting_glucose", "90", "mg/dL")]
    curr = [_make_feat("fasting_glucose", "108", "mg/dL")]

    comparisons, trajectory = compare_features(prev, curr)
    assert len(comparisons) == 1
    item = comparisons[0]
    assert item.canonical_name == "fasting_glucose"
    assert item.direction == "increased"
    assert item.absolute_change == Decimal(18)
    assert item.percentage_change == Decimal("20.00")
    assert "fasting_glucose" in trajectory.increased_features
    assert trajectory.increased_count == 1


def test_feature_decrease_calculated_correctly() -> None:
    """Test 11: Feature decreases are calculated correctly."""
    prev = [_make_feat("total_cholesterol", "200", "mg/dL")]
    curr = [_make_feat("total_cholesterol", "170", "mg/dL")]

    comparisons, trajectory = compare_features(prev, curr)
    assert len(comparisons) == 1
    item = comparisons[0]
    assert item.canonical_name == "total_cholesterol"
    assert item.direction == "decreased"
    assert item.absolute_change == Decimal(-30)
    assert item.percentage_change == Decimal("-15.00")
    assert "total_cholesterol" in trajectory.decreased_features
    assert trajectory.decreased_count == 1


def test_unchanged_values_detected() -> None:
    """Test 12: Unchanged values are detected."""
    prev = [_make_feat("creatinine", "0.90", "mg/dL"), _make_feat("sex", "male", None)]
    curr = [_make_feat("creatinine", "0.90", "mg/dL"), _make_feat("sex", "male", None)]

    comparisons, trajectory = compare_features(prev, curr)
    creat = next(c for c in comparisons if c.canonical_name == "creatinine")
    assert creat.direction == "unchanged"
    assert creat.absolute_change == Decimal("0.00")
    assert creat.percentage_change == Decimal("0.00")

    sex_feat = next(c for c in comparisons if c.canonical_name == "sex")
    assert sex_feat.direction == "unchanged"
    assert sex_feat.absolute_change is None
    assert trajectory.unchanged_count == 2


def test_percentage_change_calculated_safely() -> None:
    """Test 13: Percentage change is calculated safely with decimals."""
    prev = [_make_feat("hba1c", "5.0", "%")]
    curr = [_make_feat("hba1c", "5.5", "%")]

    comparisons, _ = compare_features(prev, curr)
    assert comparisons[0].percentage_change == Decimal("10.00")
    assert comparisons[0].absolute_change == Decimal("0.5")


def test_zero_value_percentage_changes_handled_safely() -> None:
    """Test 14: Zero-value percentage changes are handled safely without ZeroDivisionError."""
    # 0 to 0 -> 0%
    prev = [_make_feat("esr", "0", "mm/hr")]
    curr = [_make_feat("esr", "0", "mm/hr")]
    comparisons, _ = compare_features(prev, curr)
    assert comparisons[0].direction == "unchanged"
    assert comparisons[0].percentage_change == Decimal(0)

    # 0 to 10 -> undefined percentage change (None), absolute change = 10
    prev_zero = [_make_feat("esr", "0", "mm/hr")]
    curr_ten = [_make_feat("esr", "10", "mm/hr")]
    comparisons_zero, _ = compare_features(prev_zero, curr_ten)
    assert comparisons_zero[0].direction == "increased"
    assert comparisons_zero[0].absolute_change == Decimal(10)
    assert comparisons_zero[0].percentage_change is None


def test_missing_values_do_not_generate_fabricated_comparisons() -> None:
    """Test 15: Missing previous/current values do not generate fabricated comparisons."""
    # Feature present only in previous report
    prev = [_make_feat("vitamin_d", "15.5", "ng/mL")]
    curr = [_make_feat("calcium", "9.2", "mg/dL")]

    comparisons, trajectory = compare_features(prev, curr)
    assert len(comparisons) == 2

    vit_d = next(c for c in comparisons if c.canonical_name == "vitamin_d")
    assert vit_d.direction == "unavailable"
    assert vit_d.previous_value == "15.5"
    assert vit_d.current_value is None
    assert vit_d.absolute_change is None
    assert vit_d.percentage_change is None
    assert "not present in current report" in (vit_d.comparison_note or "")

    calc = next(c for c in comparisons if c.canonical_name == "calcium")
    assert calc.direction == "unavailable"
    assert calc.previous_value is None
    assert calc.current_value == "9.2"
    assert calc.absolute_change is None
    assert calc.percentage_change is None
    assert "not present in previous report" in (calc.comparison_note or "")

    assert trajectory.unavailable_count == 2
    assert trajectory.increased_count == 0
    assert trajectory.decreased_count == 0
