import { HealthStatus } from './components/HealthStatus';
import { useState } from 'react';
import { BaselineCard } from './components/BaselineCard';
import { EmptyState } from './components/EmptyState';
import { ErrorState } from './components/ErrorState';
import { Header } from './components/Header';
import { HealthSnapshot } from './components/HealthSnapshot';
import { HeroSection } from './components/HeroSection';
import { LongitudinalComparison } from './components/LongitudinalComparison';
import { ModelPlaceholder } from './components/ModelPlaceholder';
import { ProcessingSteps } from './components/ProcessingSteps';
import { ReportSummary } from './components/ReportSummary';
import { TrajectorySummary } from './components/TrajectorySummary';
import { UploadCard } from './components/UploadCard';
import { LongitudinalAnalysisResponse } from './types';

const API_BASE = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [userId, setUserId] = useState('dev-user-1');
  const [reportSeriesName, setReportSeriesName] = useState('Annual Health Checkup');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LongitudinalAnalysisResponse | null>(null);

  const scrollToUpload = () => {
    const el = document.getElementById('upload-card');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleReset = () => {
    setFile(null);
    setError(null);
    setResult(null);
  };

  const submitFile = async () => {
    if (!file) {
      setError('Please choose a PDF report first.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId.trim() || 'dev-user-1');
    formData.append('report_series_name', reportSeriesName.trim() || 'Annual Health Checkup');

    try {
      const response = await fetch(`${API_BASE}/reports/pdf/analyze`, {
        method: 'POST',
        body: formData,
      });

      const payload = (await response.json()) as LongitudinalAnalysisResponse;
      if (!response.ok) {
        throw new Error(payload?.warnings?.[0] ?? 'The backend could not process the uploaded PDF.');
      }

      setResult(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unexpected server error.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <Header userId={userId} reportSeriesName={reportSeriesName} />
      <HealthStatus />

      <main className="main-content">
        <HeroSection onCtaClick={scrollToUpload} />

        <div className="dashboard-grid">
          {/* Left Column: Upload & Config */}
          <div className="dashboard-column-left">
            <UploadCard
              userId={userId}
              setUserId={setUserId}
              reportSeriesName={reportSeriesName}
              setReportSeriesName={setReportSeriesName}
              file={file}
              setFile={setFile}
              onAnalyze={submitFile}
              loading={loading}
              onReset={handleReset}
            />

            {loading && <ProcessingSteps />}

            {error && (
              <ErrorState
                error={error}
                missingFeatures={result?.validation?.missing_required_features}
                warnings={result?.warnings}
                onRetry={() => setError(null)}
              />
            )}
          </div>

          {/* Right Column: Dynamic Results / Empty State */}
          <div className="dashboard-column-right">
            {!result && !loading && !error && <EmptyState />}

            {result && (
              <div className="results-stack">
                {/* 1. Report Analyzed Executive Summary */}
                <ReportSummary data={result} />

                {/* 2. Current Health Snapshot (Core Biomarkers, Completeness, Additional Labs) */}
                <HealthSnapshot
                  snapshot={result.snapshot}
                  extractedFeatures={result.extracted_features}
                  validation={result.validation}
                  reportId={result.report_id}
                  reportDate={result.report_date}
                  uploadedAt={result.uploaded_at}
                  pageCount={result.page_count}
                  extractionMethod={result.extraction_method}
                />

                {/* 3. First Report -> Baseline Established */}
                {result.is_baseline && <BaselineCard data={result} />}

                {/* 4. Subsequent Report -> Longitudinal Trajectory & Comparisons */}
                {!result.is_baseline && (
                  <>
                    {result.trajectory_summary && (
                      <TrajectorySummary summary={result.trajectory_summary} />
                    )}
                    {result.feature_comparisons.length > 0 && (
                      <LongitudinalComparison
                        comparisons={result.feature_comparisons}
                        currentReportId={result.report_id}
                        previousReportId={result.previous_report_id}
                      />
                    )}
                  </>
                )}

                {/* 5. Honest ML Model Placeholder */}
                <ModelPlaceholder />
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <div className="footer-container">
          <p className="footer-disclaimer">
            {result?.disclaimer ??
              'Research decision-support prototype only. HealthTrajectory converts laboratory reports into structured clinical information. It does not diagnose, provide medical treatment advice, or claim clinical validation.'}
          </p>
          <div className="footer-meta">
            <span>HealthTrajectory v0.1.0</span>
            <span>&bull;</span>
            <span>Document-Wide Tesseract OCR</span>
            <span>&bull;</span>
            <span>Zero Fabricated Data</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
