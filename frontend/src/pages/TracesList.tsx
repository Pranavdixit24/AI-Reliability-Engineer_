import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import type { ExecutionTraceResponse } from '../types';
import { TraceDetail } from './TraceDetail';

export const TracesList: React.FC = () => {
  const [traces, setTraces] = useState<ExecutionTraceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTraceId, setSelectedTraceId] = useState<number | null>(null);

  useEffect(() => {
    fetchTraces();
  }, []);

  const fetchTraces = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTraces();
      setTraces(data);
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

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Evaluated Traces</h1>
      
      {loading ? (
        <div className="flex items-center justify-center p-12">Loading traces...</div>
      ) : error ? (
        <div className="alert-warning">{error}</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Identifier</th>
                <th>Test Case ID</th>
                <th>Steps</th>
                <th>Final Response</th>
              </tr>
            </thead>
            <tbody>
              {traces.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center text-muted" style={{ padding: '2rem' }}>
                    No traces available.
                  </td>
                </tr>
              ) : (
                traces.map(trace => (
                  <tr key={trace.id} onClick={() => setSelectedTraceId(trace.id)}>
                    <td className="font-medium text-accent">#{trace.id}</td>
                    <td>{trace.trace_identifier}</td>
                    <td>{trace.test_case_id}</td>
                    <td>{trace.steps?.length || 0}</td>
                    <td className="text-sm text-muted max-w-xs truncate" style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {trace.final_response || 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
