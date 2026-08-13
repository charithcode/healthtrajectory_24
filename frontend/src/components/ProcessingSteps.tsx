import React, { useEffect, useState } from 'react';

const STEPS = [
  { id: 'upload', title: 'Uploading Document', desc: 'Securely receiving laboratory PDF' },
  { id: 'ocr', title: 'Reading Report', desc: 'Full-document Tesseract OCR across all pages' },
  { id: 'extract', title: 'Extracting Laboratory Values', desc: 'Parsing canonical biomarker names & units' },
  { id: 'validate', title: 'Validating Features', desc: 'Verifying 9 basic requirements & optional labs' },
  { id: 'trajectory', title: 'Preparing Analysis', desc: 'Establishing baseline or longitudinal comparison' },
];

export const ProcessingSteps: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card processing-card">
      <div className="processing-header">
        <div className="pulse-ring">
          <div className="pulse-core"></div>
        </div>
        <div>
          <h3 className="processing-title">Processing Laboratory Report</h3>
          <p className="processing-desc">Executing full-document OCR and clinical feature validation pipeline...</p>
        </div>
      </div>

      <div className="steps-container">
        {STEPS.map((step, index) => {
          const isCompleted = index < activeStep;
          const isActive = index === activeStep;
          const isPending = index > activeStep;

          return (
            <div
              key={step.id}
              className={`step-item ${isCompleted ? 'step-completed' : ''} ${isActive ? 'step-active' : ''} ${isPending ? 'step-pending' : ''}`}
            >
              <div className="step-indicator">
                {isCompleted ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <span className="step-num">{index + 1}</span>
                )}
              </div>
              <div className="step-content">
                <span className="step-title">{step.title}</span>
                <span className="step-desc">{step.desc}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
