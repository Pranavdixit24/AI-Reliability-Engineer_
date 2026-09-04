import React, { useState } from 'react';
import { Play, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import type { BatchEvaluationResponse } from '../types';

export const BatchEvaluation: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BatchEvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    const ids = input.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    if (ids.length === 0) {
      setError('Please enter valid trace IDs separated by commas');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);
      const res = await apiClient.runBatchEvaluation(ids);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Batch evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Controlled Batch Evaluation</h1>
      
      <div className="card max-w-2xl">
        <p className="text-muted mb-4">
          Enter trace IDs to evaluate. The backend will sequentially run Phase 5 through 8.
          Already fully-evaluated traces will be skipped automatically.
        </p>

        <div className="alert-warning mb-6">
          <AlertTriangle size={20} />
          <div>
            <strong>LLM Invocation Warning</strong>
            <p className="text-sm">
              Traces that have not completed Phase 6 (Response Truthfulness) will invoke the external 
              Groq LLM API. Please enforce batch limits and use controlled evaluation sets.
            </p>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-muted mb-2">
            Trace IDs (comma-separated, max 15)
          </label>
          <input
            type="text"
            className="input"
            placeholder="e.g. 1, 2, 3, 5"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />
        </div>

        <button 
          className="btn flex items-center gap-2"
          onClick={handleRun}
          disabled={loading || !input.trim()}
        >
          {loading ? (
             <span>Evaluating...</span>
          ) : (
            <>
              <Play size={16} />
              <span>Run Batch Evaluation</span>
            </>
          )}
        </button>

        {error && <div className="mt-4 text-red-500 text-sm">{error}</div>}

        {result && (
          <div className="mt-8 border-t border-slate-700 pt-6">
            <h3 className="font-bold text-lg mb-4">Evaluation Results</h3>
            
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-3 bg-slate-800 rounded text-center">
                <div className="text-2xl font-bold text-emerald-500">{result.completed_count}</div>
                <div className="text-sm text-muted">Completed</div>
              </div>
              <div className="p-3 bg-slate-800 rounded text-center">
                <div className="text-2xl font-bold text-slate-400">{result.skipped_count}</div>
                <div className="text-sm text-muted">Skipped</div>
              </div>
              <div className="p-3 bg-slate-800 rounded text-center">
                <div className="text-2xl font-bold text-red-500">{result.failed_count}</div>
                <div className="text-sm text-muted">Failed</div>
              </div>
            </div>

            <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-2">
              {result.results.map((res, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-800 rounded border border-slate-700">
                  <div className="font-medium">Trace #{res.trace_id}</div>
                  <div>
                    {res.status === 'COMPLETED' && <span className="badge badge-pass flex items-center gap-1"><CheckCircle size={12}/> COMPLETED</span>}
                    {res.status === 'SKIPPED' && <span className="badge badge-skipped text-xs">{res.skipped_reason || 'SKIPPED'}</span>}
                    {res.status === 'FAILED' && (
                       <div className="flex flex-col items-end gap-1">
                         <span className="badge badge-fail flex items-center gap-1"><XCircle size={12}/> FAILED</span>
                         <span className="text-xs text-red-400">{res.error}</span>
                       </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
