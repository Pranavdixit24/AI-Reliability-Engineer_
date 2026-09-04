import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import type { TraceSummary } from '../types';
import { TraceDetail } from './TraceDetail';

interface TracesListProps {
  evaluatedOnly?: boolean;
}

export const TracesList: React.FC<TracesListProps> = ({ evaluatedOnly = false }) => {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const limit = 20;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTraceId, setSelectedTraceId] = useState<number | null>(null);

  useEffect(() => {
    fetchTraces(page);
  }, [page, evaluatedOnly]);

  const fetchTraces = async (pageNum: number) => {
    try {
      setLoading(true);
      const skip = (pageNum - 1) * limit;
      const data = await apiClient.getTracesSummary(skip, limit, evaluatedOnly);
      setTraces(data.items);
      setTotal(data.total);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load traces');
    } finally {
      setLoading(false);
    }
  };

  if (selectedTraceId) {
    return (
      <TraceDetail 
        traceId={selectedTraceId} 
        onBack={() => setSelectedTraceId(null)} 
      />
    );
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">{evaluatedOnly ? 'Evaluated Traces' : 'All Traces'}</h1>
      
      {loading ? (
        <div className="flex items-center justify-center p-12">Loading traces...</div>
      ) : error ? (
        <div className="alert-warning">{error}</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Trace</th>
                <th>Test Case ID</th>
                <th>Status</th>
                {evaluatedOnly && <th>Verdict</th>}
                <th>Steps</th>
                <th>Final Response</th>
              </tr>
            </thead>
            <tbody>
              {traces.length === 0 ? (
                <tr>
                  <td colSpan={evaluatedOnly ? 6 : 5} className="text-center text-muted" style={{ padding: '2rem' }}>
                    No traces available.
                  </td>
                </tr>
              ) : (
                traces.map(trace => (
                  <tr key={trace.id} onClick={() => setSelectedTraceId(trace.id)} className="cursor-pointer hover:bg-slate-800">
                    <td className="font-medium text-accent">Trace #{trace.id}</td>
                    <td>{trace.test_case_id}</td>
                    <td>
                      {trace.is_evaluated ? (
                        <span className="badge badge-pass">Evaluated</span>
                      ) : (
                        <span className="badge badge-unknown">Not Evaluated</span>
                      )}
                    </td>
                    {evaluatedOnly && (
                      <td>
                        <span className={`badge ${trace.overall_evaluation_verdict === 'PASS' ? 'badge-pass' : trace.overall_evaluation_verdict === 'FAIL' ? 'badge-fail' : 'badge-unknown'}`}>
                          {trace.overall_evaluation_verdict || 'N/A'}
                        </span>
                      </td>
                    )}
                    <td>{trace.steps_count}</td>
                    <td className="text-sm text-muted max-w-xs truncate" style={{ maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {trace.final_response || 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-700 bg-slate-900">
              <div className="text-sm text-muted">
                Showing {((page - 1) * limit) + 1}–{Math.min(page * limit, total)} of {total} traces
              </div>
              <div className="flex items-center gap-2">
                <button 
                  className="btn text-sm py-1 px-3" 
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  Previous
                </button>
                <span className="text-sm font-medium px-2">{page} / {totalPages}</span>
                <button 
                  className="btn text-sm py-1 px-3" 
                  disabled={page === totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
