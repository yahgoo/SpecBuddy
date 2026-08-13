import type { AnalysisResponse, ClarifyOptionsResponse, HandoffExportResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function analyzeSpec(
  filename: string,
  rawText: string,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/specs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, raw_text: rawText }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Analysis failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<AnalysisResponse>;
}

export async function applyRewrite(
  specId: number,
  lineNumber: number,
  rewrittenText: string,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/specs/${specId}/rewrites`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ line_number: lineNumber, rewritten_text: rewrittenText }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Rewrite failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<AnalysisResponse>;
}

export async function removeRewrite(
  specId: number,
  lineNumber: number,
): Promise<AnalysisResponse> {
  const response = await fetch(
    `${API_BASE}/api/specs/${specId}/rewrites/${lineNumber}`,
    { method: 'DELETE' },
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Remove rewrite failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<AnalysisResponse>;
}

export async function resetRewrites(
  specId: number,
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/specs/${specId}/rewrites`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Reset rewrites failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<AnalysisResponse>;
}

export async function fetchClarifyOptions(
  specId: number,
  lineNumber: number,
  checkId: string,
): Promise<ClarifyOptionsResponse> {
  const response = await fetch(
    `${API_BASE}/api/specs/${specId}/clarify`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ line_number: lineNumber, check_id: checkId }),
    },
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Clarify failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<ClarifyOptionsResponse>;
}

export async function selectClarifyOption(
  specId: number,
  lineNumber: number,
  checkId: string,
  chosenText: string,
): Promise<AnalysisResponse> {
  const response = await fetch(
    `${API_BASE}/api/specs/${specId}/clarify/select`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        line_number: lineNumber,
        check_id: checkId,
        chosen_text: chosenText,
      }),
    },
  );

  if (response.status === 409) {
    throw new ConflictError('Line has changed — please re-clarify.');
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Select clarify option failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<AnalysisResponse>;
}

export class ConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConflictError';
  }
}

export async function exportHandoffPack(
  specId: number,
): Promise<HandoffExportResponse> {
  const response = await fetch(
    `${API_BASE}/api/specs/${specId}/handoff-export`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    },
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Export failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json() as Promise<HandoffExportResponse>;
}


// ---------------------------------------------------------------------------
// Evidence & Benchmark
// ---------------------------------------------------------------------------

export async function fetchEvidence(
  specId: number,
): Promise<import('./types').EvidenceResponse> {
  const response = await fetch(`${API_BASE}/api/specs/${specId}/evidence`);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Fetch evidence failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json();
}

export async function triggerBenchmark(): Promise<import('./types').BenchmarkRunResponse> {
  const response = await fetch(`${API_BASE}/api/benchmark/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok && response.status !== 202) {
    const detail = await response.text();
    throw new Error(
      `Benchmark failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  return response.json();
}

export async function fetchBenchmarkResults(): Promise<import('./types').BenchmarkRunResponse | null> {
  const response = await fetch(`${API_BASE}/api/benchmark/results`);

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Fetch benchmark results failed (${response.status}): ${detail || response.statusText}`,
    );
  }

  const data = await response.json();
  return data.result ?? null;
}
