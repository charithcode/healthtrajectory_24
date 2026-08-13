"""Conservative parser for document-wide medical-report text extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from app.schemas.features import ExtractedFeature, FeatureMeasurement, PageText
from app.services.feature_dictionary import (
    ALIAS_TO_CANONICAL,
    FEATURE_DEFINITIONS,
    normalize_unit_for_feature,
)

_UNIT_REGEX_PART = (
    r"mg/dL|mg/dl|mg/DL|mg/L|g/dL|g/dl|U/L|u/l|mIU/L|ng/mL|ng/ml|pg/mL|pg/ml|"
    r"mEq/L|mmol/L|mmol/l|mm/hr|mm/hour|mg/g|kg/m2|cm|kg|years?|yrs?|yr|y|%|IU/mL"
)
_DEMOGRAPHIC_GENDER_VALUES = "male|female|intersex|unknown|not disclosed"


@dataclass(frozen=True)
class ParseResult:
    features: list[ExtractedFeature] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_report_pages(
    pages: list[dict[str, str | int]] | list[PageText],
    extraction_method: str = "pdf_text",
) -> ParseResult:
    """Scan the complete document and aggregate recognized features by canonical name."""

    candidates: list[ExtractedFeature] = []
    warnings: list[str] = []

    for page in pages:
        page_number = page["page_number"] if isinstance(page, dict) else page.page_number
        text = page["text"] if isinstance(page, dict) else page.text

        lines = [line.strip() for line in str(text).splitlines()]
        lines = [line for line in lines if line]

        # 1. Parse single lines
        for line in lines:
            normalized = " ".join(line.split())
            candidates.extend(_parse_line_candidates(normalized, int(page_number), extraction_method))

        # 2. Parse adjacent lines joined by a space
        for i in range(len(lines) - 1):
            line1 = lines[i]
            line2 = lines[i + 1]
            if _is_reference_or_educational_context(" ".join(line1.split())) or \
               _is_reference_or_educational_context(" ".join(line2.split())):
                continue

            joined = line1 + " " + line2
            normalized = " ".join(joined.split())
            candidates.extend(_parse_line_candidates(normalized, int(page_number), extraction_method))

    # Group candidates by canonical name
    by_feature: dict[str, list[ExtractedFeature]] = {}
    for candidate in candidates:
        by_feature.setdefault(candidate.canonical_name, []).append(candidate)

    final_features: list[ExtractedFeature] = []
    for canonical_name, items in by_feature.items():
        # Deduplicate identical values (keeping the first occurrence)
        unique_items: list[ExtractedFeature] = []
        for item in items:
            dup = False
            for u in unique_items:
                if _values_equal(u.value, item.value):
                    dup = True
                    break
            if not dup:
                unique_items.append(item)

        if len(unique_items) == 1:
            final_features.append(unique_items[0])
        else:
            # Preserve the conflict by including all conflicting values
            final_features.extend(unique_items)

            # Report a concise warning with page numbers
            pages_str = ", ".join(str(u.source_page) for u in unique_items if u.source_page is not None)
            warnings.append(f"Conflicting values detected for '{canonical_name}' on pages {pages_str}.")

    features = sorted(final_features, key=lambda item: (item.source_page or 0, item.canonical_name))
    if not features:
        warnings.append("No configured health parameters were recognized in extracted text.")
    return ParseResult(features=features, warnings=warnings)


def parse_report_text(text: str, page_number: int = 1, extraction_method: str = "pdf_text") -> ParseResult:
    """Parse configured feature aliases from one text block."""

    return parse_report_pages([{"page_number": page_number, "text": text}], extraction_method=extraction_method)


def parsed_features_to_measurements(features: list[ExtractedFeature]) -> list[FeatureMeasurement]:
    """Adapt parsed records into the unchanged shared validation input contract."""

    return [
        FeatureMeasurement(
            name=feature.canonical_name,
            value=feature.value,
            unit=feature.unit,
            source=feature.source,
            source_page=feature.source_page,
            source_text=feature.source_text,
        )
        for feature in features
    ]


def _values_equal(left: Decimal | str, right: Decimal | str) -> bool:
    if isinstance(left, Decimal) and isinstance(right, Decimal):
        return left == right
    return str(left).lower() == str(right).lower()


def debug_parse_report_pages(
    pages: list[dict[str, str | int]] | list[PageText],
    extraction_method: str = "pdf_text",
) -> list[dict[str, object]]:
    """Return debug details for page-level candidate extraction."""

    rows: list[dict[str, object]] = []
    for page in pages:
        page_number = page["page_number"] if isinstance(page, dict) else page.page_number
        text = page["text"] if isinstance(page, dict) else page.text
        lines = [line.strip() for line in str(text).splitlines()]
        lines = [line for line in lines if line]

        for line in lines:
            normalized = " ".join(line.split())
            rows.append(
                {
                    "page_number": int(page_number),
                    "text_length": len(normalized),
                    "raw_line": line,
                    "candidates": [
                        {
                            "canonical_name": item.canonical_name,
                            "value": str(item.value),
                            "unit": item.unit,
                            "source_page": item.source_page,
                            "source_text": item.source_text,
                        }
                        for item in _parse_line_candidates(normalized, int(page_number), extraction_method)
                    ],
                    "rejected": _rejection_reasons(normalized),
                }
            )

        for i in range(len(lines) - 1):
            line1 = lines[i]
            line2 = lines[i + 1]
            if _is_reference_or_educational_context(" ".join(line1.split())) or \
               _is_reference_or_educational_context(" ".join(line2.split())):
                continue
            joined = line1 + " " + line2
            normalized = " ".join(joined.split())
            rows.append(
                {
                    "page_number": int(page_number),
                    "text_length": len(normalized),
                    "raw_line": joined,
                    "candidates": [
                        {
                            "canonical_name": item.canonical_name,
                            "value": str(item.value),
                            "unit": item.unit,
                            "source_page": item.source_page,
                            "source_text": item.source_text,
                        }
                        for item in _parse_line_candidates(normalized, int(page_number), extraction_method)
                    ],
                    "rejected": _rejection_reasons(normalized),
                }
            )
    return rows


def _rejection_reasons(line: str) -> list[str]:
    if not line:
        return ["empty line"]

    reasons: list[str] = []
    if _is_reference_or_educational_context(line):
        reasons.append("reference_or_educational_context")
    if re.search(
        r"\b(?:age|sex|gender|fasting glucose|fbs|hba1c|total cholesterol|hdl|ldl|triglycerides|creatinine|bmi)\b\s*(?:>=|<=|>|<|to|between)\s*\d",
        line,
        re.IGNORECASE,
    ):
        reasons.append("comparison_or_range")
    if not reasons:
        reasons.append("candidate_scan")
    return reasons


def _has_comparison_or_range(line: str, feature_name: str) -> bool:
    return bool(
        re.search(
            rf"\b{re.escape(feature_name)}\b\s*(?:>=|<=|>|<|to|between)\s*\d",
            line,
            re.IGNORECASE,
        )
    )


def _is_reference_or_educational_context(line: str) -> bool:
    patterns = [
        r"\b(?:reference range|expected range|clinical explanation|educational material|normal values|grading of albuminuria)\b",
        r"\b(?:age|sex|gender|fasting glucose|fbs|hba1c|total cholesterol|hdl|ldl|triglycerides|creatinine|bmi)\b\s*(?:>=|<=|>|<|to|between)\s*\d",
        r"\b(?:age|patient age|sex|gender|fasting glucose|hba1c|ldl|hdl|triglycerides|creatinine|bmi)\b\s*\b(?:measures|measurement|test|range|reference)\b",
        r"\b(?:for patients aged|older than|younger than|patients aged|aged over|aged under)\b",
        r"\b\d+\s*[-–]\s*\d+\s*(?:years?|yrs?|yr)\b",
        r"^\s*\d+\.\s+[A-Z]",
        r"\bcondition\s+_\s+mg/g\b",
        r"^\s*0\s*=\s*300",
        r"\bcyanide-free\s+sls\b",
        r"^\s*(?:deficiency|borderline|desirable|optimal|high|very high|toxicity)\s*[:\-]?\s*(?:>=|<=|>|<)\s*\d",
    ]
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _parse_line_candidates(line: str, page_number: int, extraction_method: str) -> list[ExtractedFeature]:
    if not line:
        return []

    normalized_line = " ".join(line.split())
    if _is_reference_or_educational_context(normalized_line):
        return []

    candidates: list[ExtractedFeature] = []
    candidates.extend(_parse_patient_demographic_matches(normalized_line, page_number, extraction_method))
    candidates.extend(_parse_result_context_matches(normalized_line, page_number, extraction_method))

    deduped: list[ExtractedFeature] = []
    seen: set[tuple[str, str, int]] = set()
    for candidate in candidates:
        key = (candidate.canonical_name, str(candidate.value).lower(), candidate.source_page)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _parse_patient_demographic_matches(
    line: str, page_number: int, extraction_method: str
) -> list[ExtractedFeature]:
    matches: list[ExtractedFeature] = []

    # 1. Compound demographic headers: Age/Gender: 41 Y/Male or Age / Sex : 41 Yrs / Female or Age/Gender: 41/M
    compound_pattern = re.compile(
        r"(?:patient\s+)?age\s*/\s*(?:patient\s+)?(?:sex|gender)\s*[:\-]?\s*"
        r"(?P<age_val>[+-]?\d+(?:\.\d+)?)\s*(?P<age_unit>years?|yrs?|yr|y)?\s*/\s*"
        r"(?P<sex_val>male|female|intersex|unknown|not disclosed|[mf])\b",
        re.IGNORECASE,
    )
    for match in compound_pattern.finditer(line):
        if _has_comparison_or_range(line, "age") or _has_comparison_or_range(line, "sex"):
            continue
        age_val = match.group("age_val")
        sex_val = match.group("sex_val")
        if age_val:
            try:
                age_num = Decimal(age_val)
                matches.append(
                    ExtractedFeature(
                        name="age",
                        canonical_name="age",
                        value=age_num,
                        unit="years",
                        source="pdf_text" if extraction_method == "pdf_text" else "ocr",
                        source_text=match.group(0),
                        source_page=page_number,
                        extraction_method=extraction_method,
                    )
                )
            except (InvalidOperation, TypeError):
                pass
        if sex_val:
            cat = sex_val.lower()
            if cat == "m":
                cat = "male"
            elif cat == "f":
                cat = "female"
            matches.append(
                ExtractedFeature(
                    name="sex",
                    canonical_name="sex",
                    value=cat,
                    unit=None,
                    source="pdf_text" if extraction_method == "pdf_text" else "ocr",
                    source_text=match.group(0),
                    source_page=page_number,
                    extraction_method=extraction_method,
                )
            )

    # 2. Standalone Age pattern
    if not any(existing.canonical_name == "age" for existing in matches):
        age_pattern = re.compile(
            r"\b(?:patient\s+)?age\s*[:\-]?\s*(?P<age_val>[+-]?\d+(?:\.\d+)?)\s*(?P<age_unit>years?|yrs?|yr|y)?\b",
            re.IGNORECASE,
        )
        for match in age_pattern.finditer(line):
            if _has_comparison_or_range(line, "age"):
                continue
            try:
                age_num = Decimal(match.group("age_val"))
                matches.append(
                    ExtractedFeature(
                        name="age",
                        canonical_name="age",
                        value=age_num,
                        unit="years",
                        source="pdf_text" if extraction_method == "pdf_text" else "ocr",
                        source_text=match.group(0),
                        source_page=page_number,
                        extraction_method=extraction_method,
                    )
                )
            except (InvalidOperation, TypeError):
                pass

    # 3. Standalone Sex / Gender pattern
    if not any(existing.canonical_name == "sex" for existing in matches):
        sex_pattern = re.compile(
            rf"\b(?:patient\s+)?(?:sex|gender)\s*[:\-]?\s*(?P<sex_val>{_DEMOGRAPHIC_GENDER_VALUES}|[mf])\b",
            re.IGNORECASE,
        )
        for match in sex_pattern.finditer(line):
            if _has_comparison_or_range(line, "sex"):
                continue
            cat = match.group("sex_val").lower()
            if cat == "m":
                cat = "male"
            elif cat == "f":
                cat = "female"
            matches.append(
                ExtractedFeature(
                    name="sex",
                    canonical_name="sex",
                    value=cat,
                    unit=None,
                    source="pdf_text" if extraction_method == "pdf_text" else "ocr",
                    source_text=match.group(0),
                    source_page=page_number,
                    extraction_method=extraction_method,
                )
            )

    return matches


def _parse_result_context_matches(
    line: str, page_number: int, extraction_method: str
) -> list[ExtractedFeature]:
    # Skip lines that represent calculated diagnostic ratios rather than absolute analyte measurements
    if re.search(r"\b(?:ratio|calculated)\b", line, re.IGNORECASE) and re.search(
        r"/\s*(?:hdl|ldl|sgpt|creatinine)\b", line, re.IGNORECASE
    ):
        return []
    if re.search(r"\b(?:ratio)\s*[:\-]?\s*\d", line, re.IGNORECASE):
        return []
    if re.search(r"\b\d+(?:\.\d+)?\s+Ratio\b", line, re.IGNORECASE):
        return []
    if re.search(
        r"\b(?:cholesterol\s*:\s*hdl|sgot/sgpt|bun/creatinine|urea/creatinine|hdl/ldl|ldl/hdl)\b",
        line,
        re.IGNORECASE,
    ):
        return []

    aliases = sorted(ALIAS_TO_CANONICAL, key=len, reverse=True)
    matches: list[ExtractedFeature] = []
    seen_spans: set[tuple[int, int]] = set()

    for alias in aliases:
        if alias in {"age", "sex", "gender"}:
            continue

        # Prefix lookbehinds to prevent false substring matches (e.g. Non-HDL matching HDL, VLDL matching LDL)
        if alias in {"cholesterol", "total cholesterol"}:
            prefix_guard = r"(?<!vldl\s)(?<!vldl-)(?<!non-hdl\s)(?<!non-hdl-)(?<!hdl\s)(?<!hdl-)(?<!ldl\s)(?<!ldl-)(?<!/)"
        elif alias in {"hdl", "hdl cholesterol", "hdl-cholesterol"}:
            prefix_guard = r"(?<!non-)(?<!non\s)(?<!/)"
        elif alias in {"ldl", "ldl cholesterol", "ldl-cholesterol"}:
            prefix_guard = r"(?<!v)(?<!v-)(?<!non-)(?<!/)"
        elif alias in {"creatinine", "sodium", "potassium"}:
            prefix_guard = r"(?<!urine\s)(?<!urinary\s)(?<!/)"
        else:
            prefix_guard = r"(?<!/)"

        # Regex matching label (with optional parenthetical acronym like (HbA1c), (SGOT), (25-OH))
        # followed by numeric value and optional unit
        numeric_pattern_str = (
            rf"{prefix_guard}\b(?P<label>{re.escape(alias)})\b(?:\s*\([^)]*\))?"
            rf"\s*[:\-\s=]?\s*(?P<value_num>[+-]?\d+(?:\.\d+)?)\s*(?P<unit>{_UNIT_REGEX_PART}|%)"
        )
        numeric_pattern = re.compile(numeric_pattern_str, re.IGNORECASE)

        categorical_pattern_str = (
            rf"{prefix_guard}\b(?P<label>{re.escape(alias)})\b(?:\s*\([^)]*\))?"
            rf"\s*[:\-]?\s*(?P<value_cat>male|female|intersex|unknown|not disclosed)\b"
        )
        categorical_pattern = re.compile(categorical_pattern_str, re.IGNORECASE)

        for pattern in (numeric_pattern, categorical_pattern):
            for match in pattern.finditer(line):
                if _is_reference_or_educational_context(line):
                    continue
                # Check for overlap with already seen spans
                overlap = False
                for start, end in seen_spans:
                    if max(start, match.start()) < min(end, match.end()):
                        overlap = True
                        break
                if overlap:
                    continue

                seen_spans.add((match.start(), match.end()))
                candidate = _build_feature_match(match, page_number, extraction_method)
                if candidate is not None:
                    matches.append(candidate)

    return matches


def _canonicalize_label(label: str) -> str:
    cleaned = " ".join(label.lower().replace("/", " ").split())
    cleaned = re.sub(r"^patient\s+", "", cleaned)
    cleaned = cleaned.replace("gender", "sex")
    return cleaned.strip()


def _build_feature_match(
    match: re.Match[str] | None, page_number: int, extraction_method: str
) -> ExtractedFeature | None:
    if match is None:
        return None

    raw_label = match.group("label")
    canonical_name = ALIAS_TO_CANONICAL.get(raw_label.lower())
    if canonical_name is None:
        label = _canonicalize_label(raw_label)
        canonical_name = ALIAS_TO_CANONICAL.get(label)
    if canonical_name is None:
        return None

    value_num = match.groupdict().get("value_num") or match.groupdict().get("value")
    value_cat = match.groupdict().get("value_cat")
    if value_cat is not None:
        value: Decimal | str = value_cat.lower()
        unit = None
    elif value_num is not None:
        try:
            value = Decimal(value_num)
        except (InvalidOperation, TypeError):
            return None
        raw_unit = match.groupdict().get("unit")
        unit = normalize_unit_for_feature(raw_unit, canonical_name)
    else:
        return None

    # Verify unit matching expected definition unit
    if unit:
        definition = FEATURE_DEFINITIONS.get(canonical_name)
        if definition:
            expected_unit = definition.get("unit")
            if expected_unit and str(unit).lower() == str(expected_unit).lower():
                unit = str(expected_unit)

    return ExtractedFeature(
        name=canonical_name,
        canonical_name=canonical_name,
        value=value,
        unit=unit,
        source="pdf_text" if extraction_method == "pdf_text" else "ocr",
        source_text=match.group(0),
        source_page=page_number,
        extraction_method=extraction_method,
    )

