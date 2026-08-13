import React, { useState } from 'react';
import { FEATURE_LABELS } from '../constants/featureLabels';
import { FeatureComparison } from '../types';

interface LongitudinalComparisonProps {
  comparisons: FeatureComparison[];
  currentReportId: number;
  previousReportId: number | null;
}

export const LongitudinalComparison: React.FC<LongitudinalComparisonProps> = ({
  comparisons,
  currentReportId,
  previousReportId,
}) => {
  const [filter, setFilter] = useState<'all' | 'increased' | 'decreased' | 'unchanged' | 'unavailable'>('all');

  const filteredComparisons = comparisons.filter((c) => (filter === 'all' ? true : c.direction === filter));

  return (
    <div className="card comparison-card">
      <div className="card-header comparison-header">
        <div>
          <div className="header-badge-row">
            <span className="badge badge-primary">Longitudinal Trajectory</span>
            <span className="badge-comparison-context">
              Report #{currentReportId} &larr; Report #{previousReportId}
            </span>
          </div>
          <h3 className="card-title">Biomarker Shift Analysis</h3>
          <p className="card-subtitle">
            Side-by-side mathematical deltas and percentage changes against previous report
          </p>
        </div>

        <div className="filter-button-group">
          <button
            type="button"
            className={`btn-filter ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({comparisons.length})
          </button>
          <button
            type="button"
            className={`btn-filter ${filter === 'increased' ? 'active' : ''}`}
            onClick={() => setFilter('increased')}
          >
            Increased
          </button>
          <button
            type="button"
            className={`btn-filter ${filter === 'decreased' ? 'active' : ''}`}
            onClick={() => setFilter('decreased')}
          >
            Decreased
          </button>
          <button
            type="button"
            className={`btn-filter ${filter === 'unchanged' ? 'active' : ''}`}
            onClick={() => setFilter('unchanged')}
          >
            Unchanged
          </button>
        </div>
      </div>

      <div className="table-responsive">
        <table className="trajectory-table">
          <thead>
            <tr>
              <th>Biomarker / Feature</th>
              <th>Previous Value</th>
              <th>Current Value</th>
              <th>Absolute Change</th>
              <th>Percentage Change</th>
              <th>Direction</th>
            </tr>
          </thead>
          <tbody>
            {filteredComparisons.map((item) => {
              const label = FEATURE_LABELS[item.canonical_name] ?? item.canonical_name;
              const hasPrev = item.previous_value !== null && item.previous_value !== undefined;
              const hasCurr = item.current_value !== null && item.current_value !== undefined;

              return (
                <tr key={item.canonical_name} className={`row-dir-${item.direction}`}>
                  <td className="cell-feature">
                    <strong className="feature-name">{label}</strong>
                    <span className="feature-canonical-code">{item.canonical_name}</span>
                  </td>

                  <td className="cell-value">
                    {hasPrev ? (
                      <span className="val-text">
                        {item.previous_value} <span className="unit-text">{item.unit ?? ''}</span>
                      </span>
                    ) : (
                      <span className="val-missing">&mdash;</span>
                    )}
                  </td>

                  <td className="cell-value">
                    {hasCurr ? (
                      <span className="val-text font-semibold">
                        {item.current_value} <span className="unit-text">{item.unit ?? ''}</span>
                      </span>
                    ) : (
                      <span className="val-missing">&mdash;</span>
                    )}
                  </td>

                  <td className="cell-change">
                    {item.absolute_change !== null && item.absolute_change !== undefined ? (
                      <span className={`delta-tag delta-${item.direction}`}>
                        {Number(item.absolute_change) > 0 ? '+' : ''}
                        {item.absolute_change} {item.unit ?? ''}
                      </span>
                    ) : (
                      <span className="text-muted">&mdash;</span>
                    )}
                  </td>

                  <td className="cell-pct">
                    {item.percentage_change !== null && item.percentage_change !== undefined ? (
                      <span className={`pct-tag pct-${item.direction}`}>
                        {Number(item.percentage_change) > 0 ? '+' : ''}
                        {item.percentage_change}%
                      </span>
                    ) : (
                      <span className="text-muted">&mdash;</span>
                    )}
                  </td>

                  <td className="cell-direction">
                    <span className={`dir-pill dir-pill-${item.direction}`}>
                      {item.direction === 'increased' && '▲ Increased'}
                      {item.direction === 'decreased' && '▼ Decreased'}
                      {item.direction === 'unchanged' && '● Unchanged'}
                      {item.direction === 'unavailable' && '— Unavailable'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
