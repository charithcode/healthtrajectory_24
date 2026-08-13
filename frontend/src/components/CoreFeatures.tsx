import React from 'react';
import { BASIC_REQUIRED_KEYS, FEATURE_LABELS } from '../constants/featureLabels';
import { ExtractedFeature } from '../types';

interface CoreFeaturesProps {
  extractedFeatures: ExtractedFeature[];
  missingRequired: string[];
}

export const CoreFeatures: React.FC<CoreFeaturesProps> = ({ extractedFeatures, missingRequired }) => {
  const featureMap = new Map<string, ExtractedFeature>();
  extractedFeatures.forEach((f) => featureMap.set(f.canonical_name, f));

  return (
    <div className="card core-features-card">
      <div className="card-header">
        <div className="card-header-icon icon-core">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </div>
        <div>
          <h3 className="card-title">Core Laboratory Panel (Basic Model)</h3>
          <p className="card-subtitle">9 standardized biomarkers required for foundational metabolic risk evaluation</p>
        </div>
      </div>

      <div className="core-grid">
        {BASIC_REQUIRED_KEYS.map((key) => {
          const feat = featureMap.get(key);
          const isMissing = missingRequired.includes(key);
          const label = FEATURE_LABELS[key] ?? key;

          return (
            <div key={key} className={`core-feature-tile ${isMissing ? 'tile-missing' : 'tile-detected'}`}>
              <div className="tile-top">
                <span className="tile-title">{label}</span>
                {feat?.source_page ? (
                  <span className="tile-page-tag" title="Source page from OCR">
                    Pg {feat.source_page}
                  </span>
                ) : null}
              </div>

              <div className="tile-main">
                {feat ? (
                  <div className="tile-value-wrap">
                    <span className="tile-value">{String(feat.value)}</span>
                    {feat.unit && <span className="tile-unit">{feat.unit}</span>}
                  </div>
                ) : (
                  <div className="tile-missing-wrap">
                    <span className="tile-missing-badge">Missing from Report</span>
                  </div>
                )}
              </div>

              <div className="tile-footer">
                <span className="tile-source-text">
                  {feat?.source_text ? `"${feat.source_text.slice(0, 35)}${feat.source_text.length > 35 ? '...' : ''}"` : isMissing ? 'Required for full assessment' : 'Document extraction'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
