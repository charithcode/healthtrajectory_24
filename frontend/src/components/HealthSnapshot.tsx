import React, { useState } from 'react';
import { BASIC_REQUIRED_KEYS, FEATURE_LABELS } from '../constants/featureLabels';
import { ExtractedFeature, HealthSnapshot as HealthSnapshotType, ValidationResponse } from '../types';

interface HealthSnapshotProps {
  snapshot?: HealthSnapshotType | null;
  extractedFeatures: ExtractedFeature[];
  validation: ValidationResponse;
  reportId: number;
  reportDate?: string | null;
  uploadedAt: string;
  pageCount: number;
  extractionMethod: string;
}

export const HealthSnapshot: React.FC<HealthSnapshotProps> = ({
  snapshot,
  extractedFeatures,
  validation,
  reportId,
  reportDate,
  uploadedAt,
  pageCount,
  extractionMethod,
}) => {
  const [additionalOpen, setAdditionalOpen] = useState(true);

  // Map features by canonical name
  const featureMap = new Map<string, ExtractedFeature>();
  extractedFeatures.forEach((f) => featureMap.set(f.canonical_name, f));

  // Determine core features vs additional features
  const coreFeatures = BASIC_REQUIRED_KEYS.map((key) => ({
    key,
    label: FEATURE_LABELS[key] ?? key,
    feature: featureMap.get(key),
    isMissing: validation.missing_required_features.includes(key),
  }));

  const additionalFeatures = extractedFeatures.filter(
    (f) => !BASIC_REQUIRED_KEYS.includes(f.canonical_name)
  );

  const basicCount = snapshot?.basic_feature_count ?? coreFeatures.filter((c) => !!c.feature).length;
  const totalBasic = snapshot?.total_basic_required ?? 9;
  const isComplete = validation.eligible_for_basic_model;

  const displayDate = reportDate
    ? new Date(reportDate).toLocaleDateString(undefined, { dateStyle: 'medium' })
    : uploadedAt
    ? new Date(uploadedAt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    : 'Recent upload';

  return (
    <section className="health-snapshot-section" id="health-snapshot">
      {/* 1. Snapshot Header */}
      <div className="card snapshot-header-card">
        <div className="snapshot-title-row">
          <div className="snapshot-title-group">
            <div className="snapshot-icon-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
              </svg>
            </div>
            <div>
              <div className="snapshot-tag">Active Diagnostic Capture</div>
              <h2 className="snapshot-main-title">Current Health Snapshot</h2>
              <p className="snapshot-subtitle">
                Standardized biomarker extraction from laboratory report #{reportId}
              </p>
            </div>
          </div>

          <div className="snapshot-meta-pills">
            <div className="meta-pill">
              <span className="meta-pill-label">Report Date:</span>
              <strong className="meta-pill-val">{displayDate}</strong>
            </div>
            <div className="meta-pill">
              <span className="meta-pill-label">Pages:</span>
              <strong className="meta-pill-val">{pageCount} (OCR)</strong>
            </div>
            <div className="meta-pill">
              <span className="meta-pill-label">Engine:</span>
              <strong className="meta-pill-val">{extractionMethod.toUpperCase()}</strong>
            </div>
          </div>
        </div>

        {/* 2. Report Completeness Strip */}
        <div className={`completeness-strip ${isComplete ? 'completeness-ok' : 'completeness-warning'}`}>
          <div className="completeness-left">
            <div className="completeness-score-badge">
              <span className="score-num">{basicCount}</span>
              <span className="score-denom">/{totalBasic}</span>
            </div>
            <div>
              <strong className="completeness-status-title">
                {isComplete ? 'Report Complete (9/9 Basic Features)' : 'More Information Required'}
              </strong>
              <p className="completeness-desc">
                {isComplete
                  ? 'All 9 required basic clinical parameters are detected and verified for risk modeling eligibility.'
                  : `${validation.missing_required_features.length} required basic feature(s) missing from this report.`}
              </p>
            </div>
          </div>

          {!isComplete && (
            <div className="missing-chips">
              <span className="missing-chips-label">Missing:</span>
              {validation.missing_required_features.map((m) => (
                <span key={m} className="missing-chip">
                  {FEATURE_LABELS[m] ?? m}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 3. Core Biomarker Snapshot Grid (9 Features) */}
      <div className="card core-snapshot-card">
        <div className="card-header">
          <div className="card-header-icon icon-core">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div>
            <h3 className="card-title">Core Biomarkers</h3>
            <p className="card-subtitle">Standardized 9 core laboratory features for basic predictive modeling</p>
          </div>
        </div>

        <div className="core-grid">
          {coreFeatures.map(({ key, label, feature, isMissing }) => (
            <div
              key={key}
              className={`core-feature-tile ${isMissing ? 'tile-missing' : 'tile-detected'}`}
            >
              <div className="tile-top">
                <span className="tile-title">{label}</span>
                {feature?.source_page ? (
                  <span className="tile-page-tag" title="Source page from OCR">
                    Pg {feature.source_page}
                  </span>
                ) : null}
              </div>

              <div className="tile-main">
                {feature ? (
                  <div className="tile-value-wrap">
                    <span className="tile-value">{String(feature.value)}</span>
                    {feature.unit && <span className="tile-unit">{feature.unit}</span>}
                  </div>
                ) : (
                  <div className="tile-missing-wrap">
                    <span className="tile-missing-badge">Missing from Report</span>
                  </div>
                )}
              </div>

              <div className="tile-footer">
                <span className="tile-source-text">
                  {feature?.source_text
                    ? `"${feature.source_text.slice(0, 35)}${feature.source_text.length > 35 ? '...' : ''}"`
                    : isMissing
                    ? 'Required parameter'
                    : 'Document extraction'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Additional Biomarkers Snapshot (Collapsible) */}
      {additionalFeatures.length > 0 && (
        <div className="card additional-features-card">
          <div className="collapsible-header" onClick={() => setAdditionalOpen(!additionalOpen)}>
            <div className="card-header-left">
              <div className="card-header-icon icon-additional">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </div>
              <div>
                <h3 className="card-title">
                  Additional Detected Biomarkers <span className="count-pill">{additionalFeatures.length}</span>
                </h3>
                <p className="card-subtitle">
                  Supplemental clinical laboratory values extracted and preserved in the longitudinal database
                </p>
              </div>
            </div>

            <button type="button" className="btn-toggle-collapse" aria-label="Toggle additional features">
              <svg
                className={`chevron-icon ${additionalOpen ? 'chevron-open' : ''}`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>

          {additionalOpen && (
            <div className="additional-grid">
              {additionalFeatures.map((feat) => {
                const label = FEATURE_LABELS[feat.canonical_name] ?? feat.canonical_name;
                return (
                  <div key={`${feat.canonical_name}-${feat.source_page ?? 0}`} className="additional-tile">
                    <div className="tile-top">
                      <span className="additional-title">{label}</span>
                      {feat.source_page && <span className="tile-page-tag">Pg {feat.source_page}</span>}
                    </div>
                    <div className="additional-val-row">
                      <strong className="additional-value">{String(feat.value)}</strong>
                      {feat.unit && <span className="additional-unit">{feat.unit}</span>}
                    </div>
                    {feat.source_text && (
                      <span className="additional-source">
                        "{feat.source_text.slice(0, 32)}{feat.source_text.length > 32 ? '...' : ''}"
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 5. Reference Interpretation Notice */}
      <div className="reference-notice-box">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <span>
          <strong>Reference Interpretation Note:</strong> Reference interpretation unavailable. HealthTrajectory presents direct, verified document extractions and longitudinal mathematical shifts without fabricated clinical diagnostic ranges.
        </span>
      </div>
    </section>
  );
};
