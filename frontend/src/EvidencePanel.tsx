import { useCallback, useEffect, useState } from 'react';

export interface EvidenceData {
  spec_id: number;
  initial_score: number;
  current_score: number;
  findings_resolved: number;
  questions_answered: number;
  true_positive_ratio_pct: number | null;
  detection_coverage_ratio_pct: number | null;
  benchmark_available: boolean;
}

interface EvidencePanelProps {
  specId: number | null;
  refreshTrigger: number;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function EvidencePanel({ specId, refreshTrigger }: EvidencePanelProps) {
  const [data, setData] = useState<EvidenceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvidence = useCallback(async () => {
    if (!specId) {
      setData(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/specs/${specId}/evidence`);
      if (response.status === 404) {
        setError('Spec not found or has been deleted.');
        setData(null);
        return;
      }
      if (!response.ok) {
        throw new Error(`Failed to fetch evidence (${response.status})`);
      }
      const json = await response.json();
      setData(json);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [specId]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence, refreshTrigger]);

  // Empty state: no spec analyzed yet
  if (!specId) {
    return (
      <div className="evidence-panel evidence-panel--empty">
        <h3>📊 Evidence</h3>
        <p className="evidence-empty-message">
          No analysis results yet. Analyze a spec to see evidence metrics.
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="evidence-panel evidence-panel--error">
        <h3>📊 Evidence</h3>
        <p className="evidence-error-message">{error}</p>
      </div>
    );
  }

  // Loading state
  if (loading && !data) {
    return (
      <div className="evidence-panel evidence-panel--loading">
        <h3>📊 Evidence</h3>
        <p>Loading evidence…</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const hasRewrites = data.initial_score !== data.current_score;
  const scoreImproved = data.current_score > data.initial_score;

  return (
    <div className="evidence-panel">
      <h3>📊 Evidence</h3>

      <div className="evidence-scores">
        {hasRewrites ? (
          <>
            <div className="evidence-score-item">
              <span className="evidence-label">Initial Score</span>
              <span className="evidence-value">{data.initial_score}</span>
            </div>
            <div className="evidence-score-arrow">→</div>
            <div className="evidence-score-item">
              <span className="evidence-label">Current Score</span>
              <span className={`evidence-value ${scoreImproved ? 'evidence-value--improved' : ''}`}>
                {data.current_score}
              </span>
            </div>
          </>
        ) : (
          <div className="evidence-score-item">
            <span className="evidence-label">Score</span>
            <span className="evidence-value">{data.current_score}</span>
          </div>
        )}
      </div>

      <div className="evidence-metrics">
        <div className="evidence-metric">
          <span className="evidence-label">Findings Resolved</span>
          <span className="evidence-value">{data.findings_resolved}</span>
        </div>
        <div className="evidence-metric">
          <span className="evidence-label">Questions Answered</span>
          <span className="evidence-value">{data.questions_answered}</span>
        </div>
      </div>

      <div className="evidence-benchmark">
        <h4>Benchmark Metrics</h4>
        {data.benchmark_available ? (
          <div className="evidence-metrics">
            <div className="evidence-metric">
              <span className="evidence-label">True-Positive Ratio</span>
              <span className="evidence-value">{data.true_positive_ratio_pct}%</span>
            </div>
            <div className="evidence-metric">
              <span className="evidence-label">Detection Coverage</span>
              <span className="evidence-value">{data.detection_coverage_ratio_pct}%</span>
            </div>
          </div>
        ) : (
          <p className="evidence-benchmark-placeholder">
            No benchmark recorded yet. Run a benchmark to see detection metrics.
          </p>
        )}
      </div>
    </div>
  );
}
