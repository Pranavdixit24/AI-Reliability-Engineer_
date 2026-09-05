import type {
  ExecutionTraceResponse,
  EvaluationHistoryResult,
  ReliabilityAnalyticsResponse,
  BatchEvaluationResponse,
  PaginatedTracesResponse
} from '../types';

const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/+$/, '');

export const apiClient = {
  async getTracesSummary(skip = 0, limit = 100, evaluatedOnly = false): Promise<PaginatedTracesResponse> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (evaluatedOnly) {
      params.append('evaluated_only', 'true');
    }
    const response = await fetch(`${API_BASE}/traces/summary?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch traces summary');
    return response.json();
  },

  async getTrace(traceId: number): Promise<ExecutionTraceResponse> {
    const response = await fetch(`${API_BASE}/traces/${traceId}`);
    if (!response.ok) throw new Error('Failed to fetch trace details');
    return response.json();
  },

  async getTestCase(testCaseId: number): Promise<any> {
    const response = await fetch(`${API_BASE}/test-cases/${testCaseId}`);
    if (!response.ok) throw new Error('Failed to fetch test case context');
    return response.json();
  },

  async getTraces(): Promise<ExecutionTraceResponse[]> {
    const response = await fetch(`${API_BASE}/traces`);
    if (!response.ok) throw new Error('Failed to fetch traces');
    return response.json();
  },

  async getTraceEvaluationHistory(traceId: number): Promise<EvaluationHistoryResult> {
    const response = await fetch(`${API_BASE}/evaluations/traces/${traceId}`);
    if (response.status === 404) {
        // Not all traces might have a full history endpoint response if the endpoint assumes fully evaluated ones, 
        // but phase 9 returns null for missing phases. If 404, it might mean trace not found.
        throw new Error('Trace not found or not evaluated');
    }
    if (!response.ok) throw new Error('Failed to fetch evaluation history');
    return response.json();
  },

  async getReliabilityAnalytics(): Promise<ReliabilityAnalyticsResponse> {
    const response = await fetch(`${API_BASE}/analytics/reliability`);
    if (!response.ok) throw new Error('Failed to fetch analytics');
    return response.json();
  },

  async runBatchEvaluation(traceIds: number[]): Promise<BatchEvaluationResponse> {
    const response = await fetch(`${API_BASE}/evaluations/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ trace_ids: traceIds })
    });
    
    if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to run batch evaluation');
    }
    return response.json();
  }
};
