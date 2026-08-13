import type { AnalysisResponse } from './types';

export interface Mission {
  id: string;
  label: string;
  hint: string;
  complete: boolean;
}

export function deriveMissions(result: AnalysisResponse | null): Mission[] {
  if (!result) return [];

  const earsFindings = result.findings.filter((f) =>
    f.check_id.startsWith('EARS-'),
  );

  return [
    {
      id: 'import-scanned',
      label: 'Import scanned',
      hint: 'Spec analyzed by the linter',
      complete: true,
    },
    {
      id: 'defects-cleared',
      label: 'Clear all defects',
      hint:
        result.defects === 0
          ? 'No critical defects remain'
          : `${result.defects} defect${result.defects > 1 ? 's' : ''} remaining`,
      complete: result.defects === 0,
    },
    {
      id: 'clarifications-reviewed',
      label: 'Resolve clarifications',
      hint:
        result.clarifications === 0
          ? 'All clarifications resolved'
          : `${result.clarifications} clarification${result.clarifications > 1 ? 's' : ''} remaining`,
      complete: result.clarifications === 0,
    },
    {
      id: 'ears-stable',
      label: 'Stabilize EARS format',
      hint:
        earsFindings.length === 0
          ? 'EARS patterns stable'
          : `${earsFindings.length} EARS finding${earsFindings.length > 1 ? 's' : ''} remaining`,
      complete: earsFindings.length === 0,
    },
    {
      id: 'agent-ready',
      label: 'Coding-agent-ready',
      hint:
        result.score >= 90 && result.verdict === 'CERTIFIED'
          ? 'Score ≥ 90 and CERTIFIED'
          : `Score ${result.score}/100 — need ≥ 90 + CERTIFIED`,
      complete: result.score >= 90 && result.verdict === 'CERTIFIED',
    },
  ];
}

export function missionProgress(missions: Mission[]): { done: number; total: number } {
  return {
    done: missions.filter((m) => m.complete).length,
    total: missions.length,
  };
}
