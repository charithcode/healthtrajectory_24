"""Longitudinal comparison service for evaluating multi-report trajectories."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.models.report import ReportFeature
from app.schemas.features import ExtractedFeature
from app.schemas.longitudinal import FeatureComparison, TrajectorySummary


def _to_decimal(val: object) -> Decimal | None:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val if val.is_finite() else None
    try:
        dec = Decimal(str(val).strip())
        return dec if dec.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def compare_features(
    previous_items: list[ReportFeature] | list[ExtractedFeature],
    current_items: list[ReportFeature] | list[ExtractedFeature],
) -> tuple[list[FeatureComparison], TrajectorySummary]:
    """Perform mathematical longitudinal comparison between two feature sets."""

    prev_map: dict[str, tuple[object, str | None]] = {}
    for item in previous_items:
        val = getattr(item, "value_raw", None) or getattr(item, "value", None)
        prev_map[item.canonical_name] = (val, item.unit)

    curr_map: dict[str, tuple[object, str | None]] = {}
    for item in current_items:
        val = getattr(item, "value_raw", None) or getattr(item, "value", None)
        curr_map[item.canonical_name] = (val, item.unit)

    all_features = sorted(set(prev_map.keys()) | set(curr_map.keys()))

    comparisons: list[FeatureComparison] = []
    increased_names: list[str] = []
    decreased_names: list[str] = []
    unchanged_names: list[str] = []
    unavailable_names: list[str] = []

    for name in all_features:
        has_prev = name in prev_map
        has_curr = name in curr_map

        prev_val_raw, prev_unit = prev_map.get(name, (None, None))
        curr_val_raw, curr_unit = curr_map.get(name, (None, None))
        unit = curr_unit or prev_unit

        if not has_prev:
            comparisons.append(
                FeatureComparison(
                    canonical_name=name,
                    previous_value=None,
                    current_value=str(curr_val_raw) if curr_val_raw is not None else None,
                    unit=unit,
                    absolute_change=None,
                    percentage_change=None,
                    direction="unavailable",
                    comparison_note="not available for comparison: feature was not present in previous report",
                )
            )
            unavailable_names.append(name)
            continue

        if not has_curr:
            comparisons.append(
                FeatureComparison(
                    canonical_name=name,
                    previous_value=str(prev_val_raw) if prev_val_raw is not None else None,
                    current_value=None,
                    unit=unit,
                    absolute_change=None,
                    percentage_change=None,
                    direction="unavailable",
                    comparison_note="not available for comparison: feature was not present in current report",
                )
            )
            unavailable_names.append(name)
            continue

        prev_dec = _to_decimal(prev_val_raw)
        curr_dec = _to_decimal(curr_val_raw)

        if prev_dec is None or curr_dec is None:
            # Non-numeric comparison (e.g. sex / categorical)
            if str(prev_val_raw).strip().lower() == str(curr_val_raw).strip().lower():
                direction = "unchanged"
                note = "unchanged compared with previous report"
                unchanged_names.append(name)
            else:
                direction = "unavailable"
                note = "not available for comparison: categorical value changed"
                unavailable_names.append(name)

            comparisons.append(
                FeatureComparison(
                    canonical_name=name,
                    previous_value=str(prev_val_raw),
                    current_value=str(curr_val_raw),
                    unit=unit,
                    absolute_change=None,
                    percentage_change=None,
                    direction=direction,
                    comparison_note=note,
                )
            )
            continue

        # Numeric comparison
        abs_change = curr_dec - prev_dec

        # Safe percentage change calculation
        pct_change: Decimal | None = None
        if prev_dec == Decimal(0):
            if curr_dec == Decimal(0):
                pct_change = Decimal(0)
            else:
                pct_change = None  # Undefined percentage from zero
        else:
            raw_pct = (abs_change / abs(prev_dec)) * Decimal(100)
            pct_change = raw_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if abs_change > Decimal(0):
            direction = "increased"
            note = "increased compared with previous report"
            increased_names.append(name)
        elif abs_change < Decimal(0):
            direction = "decreased"
            note = "decreased compared with previous report"
            decreased_names.append(name)
        else:
            direction = "unchanged"
            note = "unchanged compared with previous report"
            unchanged_names.append(name)

        comparisons.append(
            FeatureComparison(
                canonical_name=name,
                previous_value=prev_dec,
                current_value=curr_dec,
                unit=unit,
                absolute_change=abs_change,
                percentage_change=pct_change,
                direction=direction,
                comparison_note=note,
            )
        )

    # Sort largest changes (highest absolute percentage change, or largest absolute delta)
    numeric_comparisons = [c for c in comparisons if c.percentage_change is not None]
    largest_changes = sorted(
        numeric_comparisons,
        key=lambda c: abs(c.percentage_change) if c.percentage_change is not None else Decimal(0),
        reverse=True,
    )[:5]

    summary_parts: list[str] = []
    if increased_names:
        summary_parts.append(f"{len(increased_names)} increased")
    if decreased_names:
        summary_parts.append(f"{len(decreased_names)} decreased")
    if unchanged_names:
        summary_parts.append(f"{len(unchanged_names)} unchanged")
    if unavailable_names:
        summary_parts.append(f"{len(unavailable_names)} unavailable for comparison")

    summary_text = (
        f"Longitudinal comparison: {', '.join(summary_parts)} compared with previous report."
        if summary_parts
        else "No features available for comparison."
    )

    trajectory = TrajectorySummary(
        total_compared=len(all_features),
        increased_count=len(increased_names),
        decreased_count=len(decreased_names),
        unchanged_count=len(unchanged_names),
        unavailable_count=len(unavailable_names),
        increased_features=increased_names,
        decreased_features=decreased_names,
        unchanged_features=unchanged_names,
        unavailable_features=unavailable_names,
        largest_changes=largest_changes,
        summary_text=summary_text,
    )

    return comparisons, trajectory
