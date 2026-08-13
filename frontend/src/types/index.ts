export type Direction = 'increased' | 'decreased' | 'unchanged' | 'unavailable';

export type FeatureComparison = {
  canonical_name: string;
  previous_value: string | number | null;
  current_value: string | number | null;
  unit: string | null;
  absolute_change: number | string | null;
  percentage_change: number | string | null;
  direction: Direction;
  comparison_note: string | null;
};

export type TrajectorySummary = {
  total_compared: number;
  increased_count: number;
  decreased_count: number;
  unchanged_count: number;
  unavailable_count: number;
  increased_features: string[];
  decreased_features: string[];
  unchanged_features: string[];
  unavailable_features: string[];
  largest_changes: FeatureComparison[];
  summary_text: string;
};

export type ExtractedFeature = {
  name: string;
  canonical_name: string;
  value: string | number;
  unit: string | null;
  source: string;
  source_page?: number | null;
  source_text?: string | null;
};

export type InvalidFeature = {
  name: string;
  canonical_name?: string | null;
  reason: string;
  source_page?: number | null;
  source_text?: string | null;
};

export type NormalizedFeature = {
  canonical_name: string;
  value: string | number;
  unit: string | null;
  source: string;
};

export type ValidationResponse = {
  eligible_for_basic_model: boolean;
  required_features: string[];
  available_features: string[];
  missing_required_features: string[];
  invalid_features: InvalidFeature[];
  normalized_features: NormalizedFeature[];
  derived_features: string[];
  message: string;
  disclaimer: string;
};

export type HealthSnapshot = {
  report_id: number;
  report_date: string | null;
  page_count: number;
  extraction_method: string;
  basic_feature_count: number;
  total_basic_required: number;
  additional_feature_count: number;
  eligible_for_basic_model: boolean;
  missing_required_features: string[];
  core_features: ExtractedFeature[];
  additional_features: ExtractedFeature[];
  completeness_percentage: number | string;
  reference_interpretation_note: string;
};

export type LongitudinalAnalysisResponse = {
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
  snapshot?: HealthSnapshot | null;
  feature_comparisons: FeatureComparison[];
  trajectory_summary: TrajectorySummary | null;
  warnings: string[];
  disclaimer: string;
};

export type ProcessingStep = {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'active' | 'completed';
};
