import { ChangeEvent, useState } from 'react';

type Direction = 'increased' | 'decreased' | 'unchanged' | 'unavailable';

type FeatureComparison = {
  canonical_name: string;
  previous_value: string | number | null;
  current_value: string | number | null;
  unit: string | null;
  absolute_change: number | null;
  percentage_change: number | null;
  direction: Direction;
  comparison_note: string | null;
};

type TrajectorySummary = {
  total_compared: number;
  increased_count: number;
  decreased_count: number;
  unchanged_count: number;
  unavailable_count: number;
  increased_features: string[];
  decreased_features: string[];
  unchanged_features: string[];
  unavailable_features: string[];
  summary_text: string;
};

type ExtractedFeature = {
  name: string;
  canonical_name: string;
  value: string | number;
  unit: string | null;
  source: string;
  source_page?: number | null;
};

type ValidationResponse = {
  eligible_for_basic_model: boolean;
  required_features: string[];
  available_features: string[];
  missing_required_features: string[];
  message: string;
};

type LongitudinalAnalysisResponse = {
  report_id: number;
  user_id: string;
  report_series_name: string;
  is_baseline: boolean;
  message: string;
  uploaded_at: string;
  report_date: string | null;
  previous_report_id: number | null;
  previous_report_date: string | null;
  page_count: number;
  extraction_method: string;
  validation: ValidationResponse;
  extracted_features: ExtractedFeature[];
  feature_comparisons: FeatureComparison[];
  trajectory_summary: TrajectorySummary | null;
  warnings: string[];
  disclaimer: string;
};

const API_BASE = 'http://localhost:8000';

const FEATURE_LABELS: Record<string, string> = {
  age: 'Age',
  sex: 'Sex',
  bmi: 'BMI',
  fasting_glucose: 'Fasting glucose',
  hba1c: 'HbA1c',
  total_cholesterol: 'Total cholesterol',
  hdl: 'HDL',
  ldl: 'LDL',
  triglycerides: 'Triglycerides',
  creatinine: 'Creatinine',
  esr: 'ESR',
  calcium: 'Calcium',
  alt: 'ALT (SGPT)',
  ast: 'AST (SGOT)',
  urea: 'Urea',
  bun: 'BUN',
  potassium: 'Potassium',
  sodium: 'Sodium',
  uric_acid: 'Uric acid',
  vitamin_d: 'Vitamin D',
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [userId, setUserId] = useState('dev-user-1');
  const [reportSeriesName, setReportSeriesName] = useState('Annual Health Checkup');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LongitudinalAnalysisResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState('No file selected');

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setFile(nextFile);
    setError(null);
    setResult(null);
    if (nextFile) {
      setStatusMessage(`Selected: ${nextFile.name}`);
    } else {
      setStatusMessage('No file selected');
    }
  };

  const submitFile = async () => {
    if (!file) {
      setError('Please choose a PDF report first.');
      return;
    }

    setLoading(true);
    setError(null);
    setStatusMessage('Uploading and processing PDF with Tesseract OCR...');

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
      setStatusMessage(payload.is_baseline ? 'Baseline established' : 'Longitudinal comparison completed');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unexpected server error.';
      setError(message);
      setResult(null);
      setStatusMessage('Processing failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">HealthTrajectory</p>
          <h1>Longitudinal Patient-Report Trajectory System</h1>
        </div>
      </header>

      <main className="dashboard">
        <section className="panel upload-panel">
          <div className="panel-header">
            <h2>Upload laboratory report</h2>
          </div>

          <div className="form-group">
            <label htmlFor="user-id-input">User / Patient ID</label>
            <input
              id="user-id-input"
              type="text"
              className="text-input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="e.g. dev-user-1"
            />
          </div>

          <div className="form-group">
            <label htmlFor="series-input">Report Series Name</label>
            <input
              id="series-input"
              type="text"
              className="text-input"
              value={reportSeriesName}
              onChange={(e) => setReportSeriesName(e.target.value)}
              placeholder="e.g. Annual Health Checkup"
            />
          </div>

          <label className="upload-dropzone">
            <input type="file" accept="application/pdf" onChange={handleFileChange} />
            <span>{file ? file.name : 'Choose PDF report'}</span>
          </label>

          <button className="primary-button" onClick={submitFile} disabled={loading || !file}>
            {loading ? 'Processing OCR & Analysis...' : 'Process & Analyze Report'}
          </button>

          <div className="status-row">
            <strong>Status:</strong>
            <span>{statusMessage}</span>
          </div>

          {error && <div className="error-box">{error}</div>}
        </section>

        {result && (
          <>
            <section className="panel summary-panel">
              <div className="panel-header">
                <h2>Analysis Status</h2>
              </div>
              <div className={result.is_baseline ? 'baseline-banner' : 'comparison-banner'}>
                <strong>{result.is_baseline ? '🌱 Baseline Established' : '📊 Longitudinal Comparison'}</strong>
                <p>{result.message}</p>
              </div>

              <div className="meta-grid">
                <div className="meta-item">
                  <span className="meta-label">Report ID</span>
                  <span className="meta-val">#{result.report_id}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Patient ID</span>
                  <span className="meta-val">{result.user_id}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Report Series</span>
                  <span className="meta-val">{result.report_series_name}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Pages Processed</span>
                  <span className="meta-val">{result.page_count} (OCR)</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Basic Model Eligible</span>
                  <span className="meta-val">
                    {result.validation.eligible_for_basic_model ? '✅ Yes' : '⚠️ Missing basic labs'}
                  </span>
                </div>
              </div>

              {result.trajectory_summary && (
                <div className="trajectory-summary-box">
                  <h3>Trajectory Shift Summary</h3>
                  <div className="stat-chips">
                    <span className="chip chip-inc">⬆️ {result.trajectory_summary.increased_count} Increased</span>
                    <span className="chip chip-dec">⬇️ {result.trajectory_summary.decreased_count} Decreased</span>
                    <span className="chip chip-unchanged">⏺️ {result.trajectory_summary.unchanged_count} Unchanged</span>
                    <span className="chip chip-unavail">❓ {result.trajectory_summary.unavailable_count} Unavailable</span>
                  </div>
                  <p className="summary-narrative">{result.trajectory_summary.summary_text}</p>
                </div>
              )}
            </section>

            {result.feature_comparisons.length > 0 && (
              <section className="panel full-width-panel">
                <div className="panel-header">
                  <h2>Longitudinal Feature Comparison</h2>
                  <span className="sub-header">
                    Comparing Report #{result.report_id} vs Previous Report #{result.previous_report_id}
                  </span>
                </div>

                <div className="table-responsive">
                  <table className="comparison-table">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>Previous Value</th>
                        <th>Current Value</th>
                        <th>Absolute Change</th>
                        <th>% Change</th>
                        <th>Direction</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.feature_comparisons.map((item) => (
                        <tr key={item.canonical_name}>
                          <td>
                            <strong>{FEATURE_LABELS[item.canonical_name] ?? item.canonical_name}</strong>
                          </td>
                          <td>
                            {item.previous_value !== null ? `${item.previous_value} ${item.unit ?? ''}` : '—'}
                          </td>
                          <td>
                            {item.current_value !== null ? `${item.current_value} ${item.unit ?? ''}` : '—'}
                          </td>
                          <td>
                            {item.absolute_change !== null
                              ? `${item.absolute_change > 0 ? '+' : ''}${item.absolute_change} ${item.unit ?? ''}`
                              : '—'}
                          </td>
                          <td>
                            {item.percentage_change !== null
                              ? `${item.percentage_change > 0 ? '+' : ''}${item.percentage_change}%`
                              : '—'}
                          </td>
                          <td>
                            <span className={`direction-badge dir-${item.direction}`}>
                              {item.direction}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            <section className="panel feature-panel">
              <h3>Extracted Features in Current Report</h3>
              <ul className="feature-list">
                {result.extracted_features.map((feat) => (
                  <li key={`${feat.canonical_name}-${feat.source_page ?? 0}`}>
                    <strong>{FEATURE_LABELS[feat.canonical_name] ?? feat.canonical_name}:</strong>{' '}
                    {feat.value} {feat.unit ?? ''}{' '}
                    <span className="source-tag">pg {feat.source_page ?? 1}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="panel warnings-panel">
              <h3>Validation & Research Disclaimer</h3>
              <p className="disclaimer">{result.disclaimer}</p>
              {result.warnings.length > 0 && (
                <ul>
                  {result.warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
