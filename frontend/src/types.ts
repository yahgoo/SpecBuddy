export interface Finding {
  line_number: number;
  type: string;
  severity: string;
  message: string;
  suggested_rewrite: string;
  check_id: string;
  category: string;
}

export interface Requirement {
  line_number: number;
  raw_text: string;
  statement: string;
  section: string | null;
  uppercase_keywords: string[];
  lowercase_keywords: string[];
}

export interface Rewrite {
  line_number: number;
  rewritten_text: string;
  applied_at: string;
}

export interface ClarifyOption {
  label: 'A' | 'B';
  rewritten_text: string;
  rationale: string;
}

export interface ClarifyOptionsResponse {
  spec_id: number;
  line_number: number;
  check_id: string;
  effective_line: string;
  options: [ClarifyOption, ClarifyOption];
}

export interface AnalysisResponse {
  spec_id: number;
  filename: string;
  raw_text: string;
  effective_markdown: string;
  created_at: string;
  requirements: Requirement[];
  findings: Finding[];
  rewrites: Rewrite[];
  score: number;
  tier: string;
  verdict: string;
  exit_code: number;
  requirement_count: number;
  defects: number;
  clarifications: number;
  infos: number;
  report_markdown: string;
}

export interface HandoffExportResponse {
  spec_id: number;
  filename: string;
  score: number;
  verdict: string;
  exported_at: string;
  markdown_document: string;
}

// ---------------------------------------------------------------------------
// Evidence & Benchmark
// ---------------------------------------------------------------------------

export interface EvidenceResponse {
  spec_id: number;
  initial_score: number;
  current_score: number;
  findings_resolved: number;
  questions_answered: number;
  true_positive_ratio_pct: number | null;
  detection_coverage_ratio_pct: number | null;
  benchmark_available: boolean;
}

export interface BenchmarkCaseResult {
  id: string;
  title: string;
  difficulty: string;
  status: string;
  detected_flags: string[];
  missed_flags: string[];
  false_positives: string[];
  error: string | null;
}

export interface BenchmarkRunResponse {
  id: number;
  started_at: string;
  completed_at: string;
  total_cases: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  true_positive_ratio: number;
  detection_coverage_ratio: number;
  per_case: BenchmarkCaseResult[];
  warnings?: string[];
}
