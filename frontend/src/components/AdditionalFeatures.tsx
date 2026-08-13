import React, { useState } from 'react';
import { BASIC_REQUIRED_KEYS, FEATURE_LABELS } from '../constants/featureLabels';
import { ExtractedFeature } from '../types';

interface AdditionalFeaturesProps {
  extractedFeatures: ExtractedFeature[];
}

export const AdditionalFeatures: React.FC<AdditionalFeaturesProps> = ({ extractedFeatures }) => {
  const [isOpen, setIsOpen] = useState(true);

  // Filter out core basic required keys to show only additional / extended biomarkers
  const additional = extractedFeatures.filter((f) => !BASIC_REQUIRED_KEYS.includes(f.canonical_name));

  if (additional.length === 0) {
    return null;
  }

  return (
    <div className="card additional-features-card">
      <div className="collapsible-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="card-header-left">
          <div className="card-header-icon icon-additional">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </div>
          <div>
            <h3 className="card-title">
              Additional Detected Biomarkers <span className="count-pill">{additional.length}</span>
            </h3>
            <p className="card-subtitle">
              Supplemental clinical laboratory values extracted and preserved in the longitudinal database
            </p>
          </div>
        </div>

        <button type="button" className="btn-toggle-collapse" aria-label="Toggle additional features">
          <svg
            className={`chevron-icon ${isOpen ? 'chevron-open' : ''}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="additional-grid">
          {additional.map((feat) => {
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
  );
};
