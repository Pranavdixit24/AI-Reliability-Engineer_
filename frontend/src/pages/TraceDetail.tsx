import React, { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle, XCircle, AlertCircle, HelpCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import type { EvaluationHistoryResult } from '../types';

interface TraceDetailProps {
  traceId: number;
  onBack: () => void;
}

const getStatusBadge = (status: string) => {
  const norm = status?.toUpperCase() || 'UNKNOWN';
  if (['SUCCESS', 'TRUTHFUL', 'PASS', 'RELIABLE_SUCCESS'].includes(norm)) {
    return <span className={`badge badge-pass`}>{norm}</span>;
  }
  if (['FAILURE', 'UNTRUTHFUL', 'FAIL', 'HONEST_FAILURE', 'FALSE_SUCCESS', 'FALSE_FAILURE', 'TASK_EXECUTION_FAILURE'].includes(norm)) {
    return <span className={`badge badge-fail`}>{norm}</span>;
  }
  return <span className={`badge badge-unknown`}>{norm}</span>;
};

export const TraceDetail: React.FC<TraceDetailProps> = ({ traceId, onBack }) => {
  const [history, setHistory] = useState<EvaluationHistoryResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, [traceId]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTraceEvaluationHistory(traceId);
      setHistory(data);
      setError(null);
    } catch (err: any) {
      if (err.message.includes('Not Found') || err.message.includes('not found')) {
         setHistory({ trace_id: traceId });
         setError(null);
      } else {
         setError(err.message || 'Failed to load trace history');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-12 text-center">Loading evaluation history...</div>;
  if (error) return <div className="alert-warning"><AlertCircle /> {error}</div>;

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <button className="btn" style={{ padding: '0.4rem', backgroundColor: 'var(--panel-border)' }} onClick={onBack}>
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold">Trace #{traceId} Lifecycle</h1>
      </div>

      <div className="card phase-card">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          1. Task Success Evaluation (Phase 5)
        </h2>
        {history?.task_success ? (
          <div>
            <div className="property-row">
              <div className="property-label">Task Outcome</div>
              <div className="property-value">{getStatusBadge(history.task_success.task_success)}</div>
            </div>
            <div className="property-row">
              <div className="property-label">Determination Method</div>
              <div className="property-value font-mono text-sm">{history.task_success.determination_method}</div>
            </div>
            <div className="property-row">
              <div className="property-label">Overall Reason</div>
              <div className="property-value text-muted">{history.task_success.overall_reason}</div>
            </div>
            
            {history.task_success.operation_evaluations?.length > 0 && (
                <div className="mt-4">
                    <h3 className="font-semibold text-sm mb-2">Operation Evaluations</h3>
                    <div className="flex flex-col gap-2">
                        {history.task_success.operation_evaluations.map((op, i) => (
                            <div key={i} className="flex justify-between p-2 bg-slate-800 rounded text-sm">
                                <span>{op.operation} ({op.requirement})</span>
                                <span>{op.satisfied ? <CheckCircle size={16} className="text-emerald-500" /> : <XCircle size={16} className="text-red-500" />}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
          </div>
        ) : (
          <div className="text-muted flex items-center gap-2"><HelpCircle size={16}/> Not evaluated yet</div>
        )}
      </div>

      <div className="card phase-card">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          2. Response Truthfulness (Phase 6)
        </h2>
        {history?.response_truthfulness ? (
          <div>
            <div className="property-row">
              <div className="property-label">Truthfulness</div>
              <div className="property-value">{getStatusBadge(history.response_truthfulness.response_truthfulness)}</div>
            </div>
            <div className="property-row">
              <div className="property-label">Outcome Claim</div>
              <div className="property-value">{getStatusBadge(history.response_truthfulness.response_outcome_claim)}</div>
            </div>
            <div className="property-row">
              <div className="property-label">Reasoning</div>
              <div className="property-value text-muted">{history.response_truthfulness.reasoning_summary}</div>
            </div>
            <div className="property-row">
              <div className="property-label">Confidence</div>
              <div className="property-value font-mono text-sm">{history.response_truthfulness.confidence}</div>
            </div>
          </div>
        ) : (
          <div className="text-muted flex items-center gap-2"><HelpCircle size={16}/> Not evaluated yet</div>
        )}
      </div>

      <div className="card phase-card">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          3. Reliability Verdict (Phase 7)
        </h2>
        {history?.reliability_verdict ? (
          <div>
            <div className="property-row">
              <div className="property-label">Overall Verdict</div>
              <div className="property-value">{getStatusBadge(history.reliability_verdict.overall_evaluation_verdict)}</div>
            </div>
            <div className="property-row">
              <div className="property-label">Classification</div>
              <div className="property-value">{getStatusBadge(history.reliability_verdict.reliability_classification)}</div>
            </div>
            {history.reliability_verdict.failure_type && (
                <div className="property-row">
                  <div className="property-label">Failure Type</div>
                  <div className="property-value">{getStatusBadge(history.reliability_verdict.failure_type)}</div>
                </div>
            )}
            <div className="property-row">
              <div className="property-label">Summary</div>
              <div className="property-value text-muted">{history.reliability_verdict.summary}</div>
            </div>
          </div>
        ) : (
          <div className="text-muted flex items-center gap-2"><HelpCircle size={16}/> Not evaluated yet</div>
        )}
      </div>

      <div className="card phase-card">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          4. Failure Diagnosis (Phase 8)
        </h2>
        {history?.failure_diagnosis ? (
          <div>
            <div className="property-row">
              <div className="property-label">Root Cause</div>
              <div className="property-value"><span className="badge badge-fail">{history.failure_diagnosis.root_cause_category}</span></div>
            </div>
            <div className="property-row">
              <div className="property-label">Summary</div>
              <div className="property-value text-muted">{history.failure_diagnosis.summary}</div>
            </div>
            {history.failure_diagnosis.supporting_evidence?.length > 0 && (
                <div className="mt-4">
                    <h3 className="font-semibold text-sm mb-2">Supporting Evidence</h3>
                    <ul className="list-disc pl-5 text-sm text-muted">
                        {history.failure_diagnosis.supporting_evidence.map((ev, i) => (
                            <li key={i}>{ev}</li>
                        ))}
                    </ul>
                </div>
            )}
          </div>
        ) : (
          <div className="text-muted flex items-center gap-2">
            {history?.reliability_verdict?.reliability_classification === 'RELIABLE_SUCCESS' 
               ? <span className="text-emerald-500"><CheckCircle size={16}/> Not applicable (Reliable Success)</span> 
               : <><HelpCircle size={16}/> Not evaluated yet</>}
          </div>
        )}
      </div>

    </div>
  );
};
