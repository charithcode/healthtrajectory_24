"""Versioned MVP feature dictionary and Basic-tier validation service."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.schemas.features import (
    FeatureMeasurement,
    InvalidFeature,
    NormalizedFeature,
    ValidationResponse,
)

SAFETY_DISCLAIMER = (
    "Research decision-support prototype only. This output is not a diagnosis and "
    "does not replace clinical judgment."
)

# This provisional hackathon configuration is an engineering gate, not a clinically
# validated or medically mandatory feature list. Move it to versioned configuration
# once the dataset and target definition are finalized.
BASIC_REQUIRED_FEATURES = [
    "age",
    "sex",
    "fasting_glucose",
    "hba1c",
    "total_cholesterol",
    "hdl",
    "ldl",
    "triglycerides",
    "creatinine",
]

FEATURE_DEFINITIONS: dict[str, dict[str, object]] = {
    "age": {"aliases": {"age"}, "unit": "years", "kind": "numeric"},
    "sex": {"aliases": {"sex", "gender"}, "unit": None, "kind": "categorical"},
    "bmi": {"aliases": {"bmi", "body mass index"}, "unit": "kg/m2", "kind": "numeric"},
    "height": {"aliases": {"height", "height cm"}, "unit": "cm", "kind": "numeric"},
    "weight": {"aliases": {"weight", "weight kg"}, "unit": "kg", "kind": "numeric"},
    "fasting_glucose": {
        "aliases": {
            "fasting glucose",
            "fbs",
            "fasting blood sugar",
            "glucose fasting",
            "glucose - fasting",
            "glucose - fasting blood",
            "fasting blood glucose",
            "glucose, fasting",
        },
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "hba1c": {
        "aliases": {
            "hba1c",
            "hbalc",
            "hbatc",
            "hbaic",
            "hb a1c",
            "hb alc",
            "hb atc",
            "hb aic",
            "glycated hemoglobin",
            "glycosylated hemoglobin",
            "hemoglobin a1c",
            "hemoglobin alc",
            "glycosylated hemoglobin (hba1c)",
        },
        "unit": "%",
        "kind": "numeric",
    },
    "total_cholesterol": {
        "aliases": {"total cholesterol", "cholesterol", "serum cholesterol"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "hdl": {
        "aliases": {"hdl", "hdl cholesterol", "hdl-cholesterol", "hdl - cholesterol"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "ldl": {
        "aliases": {"ldl", "ldl cholesterol", "ldl-cholesterol", "ldl - cholesterol"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "triglycerides": {
        "aliases": {"triglycerides", "tg", "serum triglycerides"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "creatinine": {
        "aliases": {"creatinine", "serum creatinine"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "hemoglobin": {
        "aliases": {"hemoglobin", "haemoglobin", "hb", "hgb", "total hemoglobin"},
        "unit": "g/dL",
        "kind": "numeric",
    },
    "urea": {
        "aliases": {"urea", "blood urea", "serum urea"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "bun": {
        "aliases": {"bun", "blood urea nitrogen", "urea nitrogen"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "ast": {
        "aliases": {"ast", "sgot", "aspartate aminotransferase", "aspartate transaminase"},
        "unit": "U/L",
        "kind": "numeric",
    },
    "alt": {
        "aliases": {"alt", "sgpt", "alanine transaminase", "alanine aminotransferase"},
        "unit": "U/L",
        "kind": "numeric",
    },
    "uric_acid": {
        "aliases": {"uric acid", "serum uric acid"},
        "unit": "mg/dL",
        "kind": "numeric",
    },
    "tsh": {"aliases": {"tsh"}, "unit": "mIU/L", "kind": "numeric"},
    "vitamin_d": {
        "aliases": {
            "vitamin d",
            "25-oh vitamin d",
            "vitamin d (25-oh)",
            "vitamin d-25-oh",
            "25-hydroxy vitamin d",
            "25 hydroxy vitamin d",
            "vitamin d (25 - oh)",
        },
        "unit": "ng/mL",
        "kind": "numeric",
    },
    "vitamin_b12": {"aliases": {"vitamin b12", "b12"}, "unit": "pg/mL", "kind": "numeric"},
    "calcium": {"aliases": {"calcium", "serum calcium", "total calcium"}, "unit": "mg/dL", "kind": "numeric"},
    "sodium": {"aliases": {"sodium", "na", "serum sodium"}, "unit": "mEq/L", "kind": "numeric"},
    "potassium": {"aliases": {"potassium", "k", "serum potassium"}, "unit": "mEq/L", "kind": "numeric"},
    "crp": {"aliases": {"crp", "c-reactive protein"}, "unit": "mg/L", "kind": "numeric"},
    "esr": {"aliases": {"esr", "erythrocyte sedimentation rate"}, "unit": "mm/hr", "kind": "numeric"},
    "urine_albumin_acr": {
        "aliases": {
            "urine albumin",
            "acr",
            "urine albumin/creatinine ratio",
            "microalbumin/creatinine ratio",
        },
        "unit": "mg/g",
        "kind": "numeric",
    },
}

ALIAS_TO_CANONICAL = {
    alias: canonical
    for canonical, definition in FEATURE_DEFINITIONS.items()
    for alias in definition["aliases"]  # type: ignore[index]
}


UNIT_SYNONYMS: dict[str, str] = {
    "mg/dl": "mg/dL",
    "mg/l": "mg/L",
    "g/dl": "g/dL",
    "u/l": "U/L",
    "miu/l": "mIU/L",
    "ng/ml": "ng/mL",
    "pg/ml": "pg/mL",
    "meq/l": "mEq/L",
    "mm/hr": "mm/hr",
    "mm/hour": "mm/hr",
    "mg/g": "mg/g",
    "kg/m2": "kg/m2",
    "cm": "cm",
    "kg": "kg",
    "years": "years",
    "year": "years",
    "yrs": "years",
    "yr": "years",
    "y": "years",
    "%": "%",
    "iu/ml": "IU/mL",
}


def normalize_unit_for_feature(unit: str | None, canonical_name: str | None = None) -> str | None:
    """Normalize unit string casing and canonicalize standard synonyms (e.g. mm/hour -> mm/hr, mmol/L -> mEq/L)."""
    if not unit:
        return None
    unit_clean = unit.strip()
    unit_lower = unit_clean.lower()
    # Monovalent electrolyte conversion: mmol/L == mEq/L (1 mmol Na+/K+ = 1 mEq)
    if canonical_name in {"sodium", "potassium"} and unit_lower in {"mmol/l", "meq/l"}:
        return "mEq/L"
    return UNIT_SYNONYMS.get(unit_lower, unit_clean)


def _resolve_canonical_name(name: str) -> str | None:
    return ALIAS_TO_CANONICAL.get(name) or (name if name in FEATURE_DEFINITIONS else None)


def validate_basic_features(measurements: list[FeatureMeasurement]) -> ValidationResponse:
    """Normalize user values and determine whether the Basic model is eligible.

    Unsupported units, duplicate values, and missing data remain explicit. No clinical
    value is inferred; BMI is the sole derived field and only when explicit height and
    weight are both supplied in the currently supported canonical units.
    """

    # Pre-scan for duplicate/conflicting canonical names
    canonical_counts: dict[str, int] = {}
    for measurement in measurements:
        canonical_name = _resolve_canonical_name(measurement.name)
        if canonical_name:
            canonical_counts[canonical_name] = canonical_counts.get(canonical_name, 0) + 1

    normalized: dict[str, NormalizedFeature] = {}
    invalid: list[InvalidFeature] = []

    for measurement in measurements:
        canonical_name = _resolve_canonical_name(measurement.name)
        if not canonical_name:
            invalid.append(
                InvalidFeature(
                    name=measurement.name,
                    canonical_name=None,
                    reason="Unsupported feature name.",
                    source_page=measurement.source_page,
                    source_text=measurement.source_text,
                )
            )
            continue
        if canonical_counts.get(canonical_name, 0) > 1:
            invalid.append(
                InvalidFeature(
                    name=measurement.name,
                    canonical_name=canonical_name,
                    reason="Duplicate/conflicting feature supplied.",
                    source_page=measurement.source_page,
                    source_text=measurement.source_text,
                )
            )
            continue

        definition = FEATURE_DEFINITIONS[canonical_name]
        expected_unit = definition["unit"]
        kind = definition["kind"]

        if kind == "numeric":
            if not isinstance(measurement.value, Decimal):
                invalid.append(
                    InvalidFeature(
                        name=measurement.name,
                        canonical_name=canonical_name,
                        reason="A numeric value is required.",
                        source_page=measurement.source_page,
                        source_text=measurement.source_text,
                    )
                )
                continue
            if not measurement.value.is_finite():
                invalid.append(
                    InvalidFeature(
                        name=measurement.name,
                        canonical_name=canonical_name,
                        reason="Value must be finite.",
                        source_page=measurement.source_page,
                        source_text=measurement.source_text,
                    )
                )
                continue
            if measurement.value < 0:
                invalid.append(
                    InvalidFeature(
                        name=measurement.name,
                        canonical_name=canonical_name,
                        reason="Value cannot be negative.",
                        source_page=measurement.source_page,
                        source_text=measurement.source_text,
                    )
                )
                continue
            norm_unit = normalize_unit_for_feature(measurement.unit, canonical_name)
            if norm_unit != expected_unit:
                invalid.append(
                    InvalidFeature(
                        name=measurement.name,
                        canonical_name=canonical_name,
                        reason=f"Unsupported unit. Expected {expected_unit}; conversion is not configured yet.",
                        source_page=measurement.source_page,
                        source_text=measurement.source_text,
                    )
                )
                continue
            unit_to_record = norm_unit
        elif not isinstance(measurement.value, str) or not measurement.value.strip():
            invalid.append(
                InvalidFeature(
                    name=measurement.name,
                    canonical_name=canonical_name,
                    reason="A non-empty categorical value is required.",
                    source_page=measurement.source_page,
                    source_text=measurement.source_text,
                )
            )
            continue
        else:
            unit_to_record = measurement.unit

        normalized[canonical_name] = NormalizedFeature(
            canonical_name=canonical_name,
            value=measurement.value,
            unit=unit_to_record,
            source=measurement.source,
        )

    derived_features = _derive_bmi_when_possible(normalized, invalid)
    missing = [feature for feature in BASIC_REQUIRED_FEATURES if feature not in normalized]
    eligible = not missing
    message = (
        "Basic model input is complete and eligible for the next prediction step."
        if eligible
        else "Prediction unavailable: enter or upload the missing Basic features."
    )

    return ValidationResponse(
        eligible_for_basic_model=eligible,
        required_features=BASIC_REQUIRED_FEATURES,
        available_features=sorted(normalized),
        missing_required_features=missing,
        invalid_features=invalid,
        normalized_features=list(normalized.values()),
        derived_features=derived_features,
        message=message,
        disclaimer=SAFETY_DISCLAIMER,
    )


def _derive_bmi_when_possible(
    normalized: dict[str, NormalizedFeature], invalid: list[InvalidFeature]
) -> list[str]:
    if "bmi" in normalized or "height" not in normalized or "weight" not in normalized:
        return []

    try:
        height_cm = Decimal(normalized["height"].value)
        weight_kg = Decimal(normalized["weight"].value)
        if height_cm <= 0 or weight_kg <= 0:
            raise InvalidOperation
        height_m = height_cm / Decimal(100)
        bmi = (weight_kg / (height_m * height_m)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        invalid.append(InvalidFeature(name="bmi", reason="BMI could not be calculated from height and weight."))
        return []

    normalized["bmi"] = NormalizedFeature(
        canonical_name="bmi", value=bmi, unit="kg/m2", source="derived"
    )
    return ["bmi"]
