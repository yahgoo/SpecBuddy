import { useCallback, useRef, useState } from 'react';
import type { AnalysisResponse, ClarifyOptionsResponse, Finding } from './types';
import {
  analyzeSpec,
  applyRewrite,
  ConflictError,
  exportHandoffPack,
  fetchClarifyOptions,
  removeRewrite,
  resetRewrites,
  selectClarifyOption,
} from './api';
import { deriveMissions, missionProgress } from './gamification';
import EvidencePanel from './EvidencePanel';

const DEMO_SME_BRIEF = `# Ah Tan Nasi Lemak Online Ordering Brief

Draft from owner after WhatsApp discussion. This is the first pass for an ordering site for our stall at a heartland coffee shop near Tampines.

## Requirements

1. The system should let customers browse nasi lemak sets, drinks, add-ons, and SGD prices quickly.
2. Customers can choose pickup or delivery and it should be user-friendly for aunties and office workers.
3. THE System SHALL support PayNow QR payment fast.
4. If PayNow payment fails, the system should retry quickly.
5. Payment receipts are sent to the customer after payment is verified.
6. THE System SHALL support English/Malay notices where possible.
7. THE System SHALL handle PDPA consent appropriately.
8. THE System SHALL delete old customer data after a reasonable period.
9. THE System SHALL use a 3km/5km delivery radius depending on rain and rider availability.
10. THE System SHALL cancel unpaid orders.
11. THE System SHALL notify customer/admin when the stall accepts the order.
12. THE System SHALL handle chilli requests as usual.
`;

type Severity = 'defect' | 'clarification' | 'info';

const SEVERITY_LABELS: Record<Severity, string> = {
  defect: 'Defect',
  clarification: 'Clarification',
  info: 'Info',
};

// ---------------------------------------------------------------------------
// Clarify panel state
// ---------------------------------------------------------------------------

interface ClarifyPanelState {
  /** The finding this panel belongs to (for key + button ref lookup) */
  findingKey: string;
  lineNumber: number;
  checkId: string;
  /** null while loading options */
  options: ClarifyOptionsResponse | null;
  /** 'loading' = fetching options; 'applying' = applying choice; null = idle */
  status: 'loading' | 'applying' | null;
  /** inline error message, if any */
  error: string | null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function App() {
  const [filename, setFilename] = useState('sme-brief.md');
  const [rawText, setRawText] = useState(DEMO_SME_BRIEF);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all');
  const [rewriteLoading, setRewriteLoading] = useState<number | null>(null);
  const [rewriteError, setRewriteError] = useState<string | null>(null);

  // Clarify panel: at most one panel open at a time
  const [clarifyPanel, setClarifyPanel] = useState<ClarifyPanelState | null>(null);

  // Export handoff state
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Evidence panel refresh trigger — increments on each rewrite/analysis cycle
  const [evidenceRefresh, setEvidenceRefresh] = useState(0);

  // Refs: panel container (for focus-on-open) and clarify button refs (for focus-on-close)
  const panelRef = useRef<HTMLDivElement | null>(null);
  const clarifyBtnRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  // Shared busy guard: any rewrite or clarify or export operation locks all action buttons
  const isBusy = rewriteLoading !== null || clarifyPanel?.status === 'loading' || clarifyPanel?.status === 'applying' || exportLoading;

  // ---------------------------------------------------------------------------
  // Analyze
  // ---------------------------------------------------------------------------

  const handleAnalyze = async () => {
    if (!rawText.trim()) {
      setError('Please paste requirements text before analyzing.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    setClarifyPanel(null);
    setExportError(null);
    try {
      const data = await analyzeSpec(filename.trim() || 'requirements.md', rawText);
      setResult(data);
      setEvidenceRefresh((n) => n + 1);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to reach the SpecBuddy backend. Is it running on localhost:8000?',
      );
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Rewrite handlers
  // ---------------------------------------------------------------------------

  const handleApplyRewrite = async (lineNumber: number, rewrittenText: string) => {
    if (!result) return;
    setRewriteLoading(lineNumber);
    setRewriteError(null);
    setClarifyPanel(null);
    try {
      const data = await applyRewrite(result.spec_id, lineNumber, rewrittenText);
      setResult(data);
      setEvidenceRefresh((n) => n + 1);
    } catch (err) {
      setRewriteError(err instanceof Error ? err.message : 'Failed to apply rewrite.');
    } finally {
      setRewriteLoading(null);
    }
  };

  const handleRemoveRewrite = async (lineNumber: number) => {
    if (!result) return;
    setRewriteLoading(lineNumber);
    setRewriteError(null);
    try {
      const data = await removeRewrite(result.spec_id, lineNumber);
      setResult(data);
      setEvidenceRefresh((n) => n + 1);
    } catch (err) {
      setRewriteError(err instanceof Error ? err.message : 'Failed to remove rewrite.');
    } finally {
      setRewriteLoading(null);
    }
  };

  const handleResetRewrites = async () => {
    if (!result) return;
    setRewriteLoading(-1);
    setRewriteError(null);
    setClarifyPanel(null);
    try {
      const data = await resetRewrites(result.spec_id);
      setResult(data);
      setEvidenceRefresh((n) => n + 1);
    } catch (err) {
      setRewriteError(err instanceof Error ? err.message : 'Failed to reset rewrites.');
    } finally {
      setRewriteLoading(null);
    }
  };

  // ---------------------------------------------------------------------------
  // Export handoff pack
  // ---------------------------------------------------------------------------

  const handleExportHandoff = async () => {
    if (!result || exportLoading) return;
    setExportLoading(true);
    setExportError(null);
    try {
      const data = await exportHandoffPack(result.spec_id);
      // Trigger browser download via Blob + Object URL
      const blob = new Blob([data.markdown_document], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      const downloadName = data.filename
        ? data.filename.replace(/\.md$/, '') + '-handoff.md'
        : 'handoff-export.md';
      anchor.href = url;
      anchor.download = downloadName;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Export failed due to network error.';
      if (msg.includes('404')) {
        setExportError('Export failed: spec not found.');
      } else {
        setExportError(msg);
      }
    } finally {
      setExportLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Clarify: open panel
  // ---------------------------------------------------------------------------

  const handleClarify = useCallback(
    async (f: Finding) => {
      if (!result || isBusy) return;
      const key = `${f.check_id}-${f.line_number}`;

      // Open panel in loading state immediately
      setClarifyPanel({
        findingKey: key,
        lineNumber: f.line_number,
        checkId: f.check_id,
        options: null,
        status: 'loading',
        error: null,
      });

      // Focus will be set after render via callback ref — handled in panelRef callback below
      try {
        const data = await fetchClarifyOptions(result.spec_id, f.line_number, f.check_id);
        setClarifyPanel((prev) =>
          prev?.findingKey === key
            ? { ...prev, options: data, status: null, error: null }
            : prev,
        );
        // Focus panel after options load
        requestAnimationFrame(() => panelRef.current?.focus());
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load clarify options.';
        setClarifyPanel(null);
        setRewriteError(msg);
        // Return focus to clarify button
        clarifyBtnRefs.current.get(key)?.focus();
      }
    },
    [result, isBusy],
  );

  // ---------------------------------------------------------------------------
  // Clarify: select option
  // ---------------------------------------------------------------------------

  const handleSelectOption = useCallback(
    async (chosenText: string) => {
      if (!result || !clarifyPanel) return;
      const { lineNumber, checkId, findingKey } = clarifyPanel;

      setClarifyPanel((prev) => (prev ? { ...prev, status: 'applying', error: null } : prev));

      try {
        const data = await selectClarifyOption(result.spec_id, lineNumber, checkId, chosenText);
        // Single setState: replace entire analysis state in one render cycle
        setResult(data);
        setEvidenceRefresh((n) => n + 1);
        setClarifyPanel(null);
        setRewriteError(null);
      } catch (err) {
        if (err instanceof ConflictError) {
          setClarifyPanel(null);
          setRewriteError('Line has changed — please re-clarify.');
        } else {
          const msg = err instanceof Error ? err.message : 'Failed to apply clarify option.';
          setClarifyPanel(null);
          setRewriteError(msg);
        }
        // Return focus to clarify button
        clarifyBtnRefs.current.get(findingKey)?.focus();
      }
    },
    [result, clarifyPanel],
  );

  // ---------------------------------------------------------------------------
  // Clarify: cancel
  // ---------------------------------------------------------------------------

  const handleClarifyCancel = useCallback(() => {
    if (!clarifyPanel) return;
    const key = clarifyPanel.findingKey;
    setClarifyPanel(null);
    // Return focus to the Clarify button that opened this panel
    requestAnimationFrame(() => clarifyBtnRefs.current.get(key)?.focus());
  }, [clarifyPanel]);

  // ---------------------------------------------------------------------------
  // Clarify panel keyboard handler (Escape = cancel)
  // ---------------------------------------------------------------------------

  const handlePanelKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClarifyCancel();
      }
    },
    [handleClarifyCancel],
  );

  // ---------------------------------------------------------------------------
  // Derived state
  // ---------------------------------------------------------------------------

  const filteredFindings: Finding[] = result
    ? severityFilter === 'all'
      ? result.findings
      : result.findings.filter((f) => f.severity === severityFilter)
    : [];

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const renderClarifyPanel = (f: Finding, key: string) => {
    if (!clarifyPanel || clarifyPanel.findingKey !== key) return null;
    const { options, status, error: panelError } = clarifyPanel;
    const isApplying = status === 'applying';

    return (
      <div
        ref={panelRef}
        className="clarify-panel"
        role="region"
        aria-label={`Clarify options for ${f.check_id} on line ${f.line_number}`}
        tabIndex={-1}
        onKeyDown={handlePanelKeyDown}
      >
        {status === 'loading' && (
          <p className="clarify-panel__loading" aria-live="polite">
            Loading…
          </p>
        )}

        {panelError && (
          <p className="clarify-panel__error" role="alert">
            {panelError}
          </p>
        )}

        {options && !panelError && (
          <>
            <div className="clarify-panel__effective-line">
              <span className="clarify-panel__effective-label">Effective line:</span>
              <code className="clarify-panel__effective-code">{options.effective_line}</code>
            </div>

            <div className="clarify-panel__options">
              {options.options.map((opt) => (
                <div
                  key={opt.label}
                  className="clarify-option-card"
                  aria-label={`Option ${opt.label}`}
                >
                  <div className="clarify-option-card__header">
                    <span className="clarify-option-card__badge">Option {opt.label}</span>
                  </div>
                  <code className="clarify-option-card__text">{opt.rewritten_text}</code>
                  <p className="clarify-option-card__rationale">{opt.rationale}</p>
                </div>
              ))}
            </div>

            <div className="clarify-panel__actions" role="group" aria-label="Choose an option">
              <button
                className="btn btn-sm btn-apply"
                disabled={isApplying}
                aria-label="Select Option A"
                onClick={() => handleSelectOption(options.options[0].rewritten_text)}
              >
                {isApplying ? 'Applying…' : 'Select A'}
              </button>
              <button
                className="btn btn-sm btn-apply"
                disabled={isApplying}
                aria-label="Select Option B"
                onClick={() => handleSelectOption(options.options[1].rewritten_text)}
              >
                {isApplying ? 'Applying…' : 'Select B'}
              </button>
              <button
                className="btn btn-sm btn-cancel"
                disabled={isApplying}
                aria-label="Cancel clarify"
                onClick={handleClarifyCancel}
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    );
  };

  // ---------------------------------------------------------------------------
  // JSX
  // ---------------------------------------------------------------------------

  return (
    <div className="app">
      <header className="header">
        <h1 className="header-title">SpecBuddy</h1>
        <span className="header-subtitle">Requirements Quality Gate</span>
      </header>

      <main className="main">
        {/* Left panel: Import */}
        <section className="panel panel-import">
          <h2 className="panel-title">Import Spec</h2>
          <label className="field-label" htmlFor="filename">
            Filename
          </label>
          <input
            id="filename"
            className="input"
            type="text"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            placeholder="requirements.md"
          />
          <label className="field-label" htmlFor="spec-text">
            Requirements Markdown
          </label>
          <textarea
            id="spec-text"
            className="textarea"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder={DEMO_SME_BRIEF}
            rows={14}
          />
          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </section>

        {/* Right panel: Results */}
        <section className="panel panel-results">
          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
            </div>
          )}

          {!result && !error && !loading && (
            <div className="empty-state">
              <p>
                Paste a requirements spec and click <strong>Analyze</strong> to see quality results.
              </p>
            </div>
          )}

          {loading && (
            <div className="empty-state">
              <p>Running deterministic checks…</p>
            </div>
          )}

          {result && (
            <>
              {/* Score card */}
              <div className={`score-card score-${result.verdict.toLowerCase()}`}>
                <div className="score-number">{result.score}</div>
                <div className="score-meta">
                  <span className={`verdict-badge verdict-${result.verdict.toLowerCase()}`}>
                    {result.verdict}
                  </span>
                  <span className="tier-label">Tier: {result.tier}</span>
                </div>
              </div>

              {/* Stats row */}
              <div className="stats-row">
                <div className="stat">
                  <span className="stat-value">{result.requirement_count}</span>
                  <span className="stat-label">Requirements</span>
                </div>
                <div className="stat stat-defect">
                  <span className="stat-value">{result.defects}</span>
                  <span className="stat-label">Defects</span>
                </div>
                <div className="stat stat-clarification">
                  <span className="stat-value">{result.clarifications}</span>
                  <span className="stat-label">Clarifications</span>
                </div>
                <div className="stat stat-info">
                  <span className="stat-value">{result.infos}</span>
                  <span className="stat-label">Info</span>
                </div>
              </div>

              {/* Evidence Panel */}
              <EvidencePanel
                specId={result.spec_id}
                refreshTrigger={evidenceRefresh}
              />

              {/* Mission Board */}
              {(() => {
                const missions = deriveMissions(result);
                const progress = missionProgress(missions);
                const agentReady = missions.find((m) => m.id === 'agent-ready')?.complete ?? false;
                return (
                  <div className="mission-board">
                    <div className="mission-board-header">
                      <h3>Mission Board</h3>
                      <span className="mission-progress">
                        {progress.done}/{progress.total}
                      </span>
                    </div>
                    <div className="mission-meter">
                      <div
                        className="mission-meter-fill"
                        style={{ width: `${(progress.done / progress.total) * 100}%` }}
                      />
                    </div>
                    {agentReady && (
                      <div className="quest-banner">
                        Agent-ready — spec meets certification threshold
                      </div>
                    )}
                    <ul className="mission-list">
                      {missions.map((m) => (
                        <li
                          key={m.id}
                          className={`mission-item ${m.complete ? 'mission-complete' : 'mission-pending'}`}
                        >
                          <span className="mission-check">{m.complete ? '✓' : '○'}</span>
                          <span className="mission-label">{m.label}</span>
                          <span className="mission-hint">{m.hint}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })()}

              {/* Findings */}
              <div className="findings-section">
                <div className="findings-header">
                  <h3>Findings ({filteredFindings.length})</h3>
                  <select
                    className="select"
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value as Severity | 'all')}
                  >
                    <option value="all">All severities</option>
                    <option value="defect">Defects</option>
                    <option value="clarification">Clarifications</option>
                    <option value="info">Info</option>
                  </select>
                </div>

                {filteredFindings.length === 0 ? (
                  <p className="no-findings">No findings for this filter.</p>
                ) : (
                  <ul className="findings-list">
                    {filteredFindings.map((f, i) => {
                      const key = `${f.check_id}-${f.line_number}-${i}`;
                      const clarifyKey = `${f.check_id}-${f.line_number}`;
                      const isPanelOpen =
                        clarifyPanel?.findingKey === clarifyKey;
                      const isThisLineApplying =
                        (clarifyPanel?.findingKey === clarifyKey &&
                          clarifyPanel.status === 'applying') ||
                        rewriteLoading === f.line_number;

                      return (
                        <li
                          key={key}
                          className={`finding finding-${f.severity}`}
                        >
                          <div className="finding-top">
                            <span className={`badge badge-${f.severity}`}>
                              {SEVERITY_LABELS[f.severity as Severity] ?? f.severity}
                            </span>
                            <span className="finding-check">{f.check_id}</span>
                            <span className="finding-line">Line {f.line_number}</span>
                          </div>

                          <p className="finding-message">{f.message}</p>

                          {/* Action bar */}
                          <div className="finding-actions">
                            {f.suggested_rewrite && (
                              <div className="finding-rewrite-action">
                                <code className="finding-suggestion">
                                  {f.suggested_rewrite}
                                </code>
                                <button
                                  className="btn btn-sm btn-apply"
                                  disabled={isBusy}
                                  onClick={() =>
                                    handleApplyRewrite(f.line_number, f.suggested_rewrite)
                                  }
                                >
                                  {isThisLineApplying ? 'Applying…' : 'Apply fix'}
                                </button>
                              </div>
                            )}

                            {/* Clarify button */}
                            <button
                              ref={(el) => {
                                if (el) clarifyBtnRefs.current.set(clarifyKey, el);
                                else clarifyBtnRefs.current.delete(clarifyKey);
                              }}
                              className="btn btn-sm btn-clarify"
                              disabled={isBusy}
                              aria-expanded={isPanelOpen}
                              aria-controls={isPanelOpen ? `clarify-panel-${clarifyKey}` : undefined}
                              aria-label={`Clarify finding ${f.check_id} on line ${f.line_number}`}
                              onClick={() => handleClarify(f)}
                            >
                              {clarifyPanel?.findingKey === clarifyKey &&
                              clarifyPanel.status === 'loading'
                                ? 'Loading…'
                                : 'Clarify'}
                            </button>
                          </div>

                          {/* Inline A/B chooser panel */}
                          {isPanelOpen && (
                            <div id={`clarify-panel-${clarifyKey}`}>
                              {renderClarifyPanel(f, clarifyKey)}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              {/* Accepted rewrites */}
              {result.rewrites.length > 0 && (
                <div className="rewrites-section">
                  <div className="rewrites-header">
                    <h3>Accepted Rewrites ({result.rewrites.length})</h3>
                    <button
                      className="btn btn-sm btn-danger"
                      disabled={isBusy}
                      onClick={handleResetRewrites}
                    >
                      {rewriteLoading === -1 ? 'Resetting…' : 'Reset all'}
                    </button>
                  </div>
                  <ul className="rewrites-list">
                    {result.rewrites.map((rw) => (
                      <li key={rw.line_number} className="rewrite-item">
                        <span className="rewrite-line">L{rw.line_number}</span>
                        <code className="rewrite-text">{rw.rewritten_text}</code>
                        <button
                          className="btn btn-sm btn-remove"
                          disabled={isBusy}
                          onClick={() => handleRemoveRewrite(rw.line_number)}
                        >
                          {rewriteLoading === rw.line_number ? 'Removing…' : 'Remove'}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Export Handoff Pack */}
              <div className="export-section">
                <button
                  className="btn export-btn"
                  disabled={isBusy}
                  aria-busy={exportLoading}
                  onClick={handleExportHandoff}
                >
                  {exportLoading ? 'Exporting…' : 'Export Handoff Pack'}
                </button>
                {exportError && (
                  <p className="export-error" aria-live="polite" role="alert">
                    {exportError}
                  </p>
                )}
              </div>

              {rewriteError && (
                <div className="alert alert-error" role="alert">
                  <strong>Error:</strong> {rewriteError}
                </div>
              )}

              {/* Requirements list */}
              <details className="details-block">
                <summary>Parsed Requirements ({result.requirements.length})</summary>
                <ul className="req-list">
                  {result.requirements.map((r) => (
                    <li key={r.line_number} className="req-item">
                      <span className="req-line">L{r.line_number}</span>
                      <span className="req-text">{r.raw_text}</span>
                    </li>
                  ))}
                </ul>
              </details>

              {/* Report preview */}
              <details className="details-block">
                <summary>Full Report (Markdown)</summary>
                <pre className="report-pre">{result.report_markdown}</pre>
              </details>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
