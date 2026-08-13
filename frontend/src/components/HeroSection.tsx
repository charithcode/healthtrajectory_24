import React from 'react';

interface HeroSectionProps {
  onCtaClick: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onCtaClick }) => {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-badge">
          <span className="spark-dot"></span>
          Document-Wide Tesseract OCR & Longitudinal Biomarker Tracking
        </div>
        <h1 className="hero-title">
          Track your health. <br />
          <span className="gradient-text">Understand your trajectory.</span>
        </h1>
        <p className="hero-subtitle">
          HealthTrajectory converts complex multi-page laboratory PDF reports into structured clinical information
          and tracks mathematical shifts between reports over time without fabricated predictions.
        </p>

        <div className="hero-actions">
          <button className="btn btn-primary" onClick={onCtaClick}>
            <svg
              className="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Upload Lab Report
          </button>
        </div>

        <div className="hero-trust-grid">
          <div className="trust-item">
            <span className="trust-icon">🔍</span>
            <div>
              <strong>100% Data-Driven</strong>
              <span>Zero fabricated values</span>
            </div>
          </div>
          <div className="trust-item">
            <span className="trust-icon">🌱</span>
            <div>
              <strong>Personal Baseline</strong>
              <span>Establish first-report anchor</span>
            </div>
          </div>
          <div className="trust-item">
            <span className="trust-icon">📊</span>
            <div>
              <strong>Trajectory Shifts</strong>
              <span>Precise mathematical deltas</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
