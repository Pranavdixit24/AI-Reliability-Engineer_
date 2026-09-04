import type {
  ExecutionTraceResponse,
  EvaluationHistoryResult,
  ReliabilityAnalyticsResponse,
  BatchEvaluationResponse
} from '../types';

const API_BASE = '/api';

export const apiClient = {
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
