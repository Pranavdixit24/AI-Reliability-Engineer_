import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { apiClient } from '../api/client';
import type { ReliabilityAnalyticsResponse } from '../types';
import { AlertCircle, CheckCircle, Target, Database } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<ReliabilityAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getReliabilityAnalytics();
      setAnalytics(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full">Loading analytics...</div>;
  if (error) return <div className="alert-warning m-4"><AlertCircle /> {error}</div>;
  if (!analytics || analytics.total_evaluated_traces === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted">
        <Database size={48} className="mb-4 opacity-50" />
        <h2 className="text-xl font-semibold mb-2">No Evaluated Traces</h2>
        <p>Run a batch evaluation to start seeing reliability analytics.</p>
      </div>
    );
  }

  // Format data for charts
  const passFailData = [
    { name: 'PASS', value: analytics.verdict_counts['PASS'] || 0, color: 'var(--status-pass)' },
    { name: 'FAIL', value: analytics.verdict_counts['FAIL'] || 0, color: 'var(--status-fail)' }
  ];

  const classificationData = Object.entries(analytics.reliability_classification_counts).map(([key, val]) => {
    let color = 'var(--status-unknown)';
    if (key === 'RELIABLE_SUCCESS') color = 'var(--status-pass)';
    else if (['HONEST_FAILURE', 'FALSE_SUCCESS', 'FALSE_FAILURE'].includes(key)) color = 'var(--status-fail)';
    return { name: key, value: val, color };
  });

  const failureTypeData = Object.entries(analytics.failure_type_counts).map(([name, value]) => ({ name, value }));

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Reliability Analytics</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-blue-500 bg-opacity-10 rounded-full text-blue-500">
            <Target size={24} style={{ color: 'var(--accent-primary)' }} />
          </div>
          <div>
            <p className="text-sm text-muted">Total Evaluated</p>
            <p className="text-2xl font-bold">{analytics.total_evaluated_traces}</p>
          </div>
        </div>
        
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-emerald-500 bg-opacity-10 rounded-full text-emerald-500">
            <CheckCircle size={24} style={{ color: 'var(--status-pass)' }} />
          </div>
          <div>
            <p className="text-sm text-muted">Overall PASS</p>
            <p className="text-2xl font-bold text-emerald-500">{analytics.verdict_counts['PASS'] || 0}</p>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="p-3 bg-red-500 bg-opacity-10 rounded-full text-red-500">
            <AlertCircle size={24} style={{ color: 'var(--status-fail)' }} />
          </div>
          <div>
            <p className="text-sm text-muted">Overall FAIL</p>
            <p className="text-2xl font-bold text-red-500">{analytics.verdict_counts['FAIL'] || 0}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Pass/Fail Pie */}
        <div className="card">
          <h2 className="font-semibold mb-4">Overall Verdicts</h2>
          <div style={{ height: 300, minHeight: 300, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={passFailData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {passFailData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--panel-border)' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Classification Pie */}
        <div className="card">
          <h2 className="font-semibold mb-4">Reliability Classifications</h2>
          <div style={{ height: 300, minHeight: 300, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={classificationData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {classificationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--panel-border)' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Failure Types Bar Chart */}
        <div className="card w-full overflow-hidden">
          <h2 className="font-semibold mb-4">Failure Types</h2>
          <div style={{ height: 300, minHeight: 300, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={failureTypeData} layout="vertical" margin={{ left: 0, right: 20, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--panel-border)" horizontal={true} vertical={false} />
                <XAxis type="number" stroke="var(--text-secondary)" />
                <YAxis dataKey="name" type="category" stroke="var(--text-secondary)" width={210} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--panel-bg)', borderColor: 'var(--panel-border)' }} cursor={{ fill: 'var(--panel-border)' }} />
                <Bar dataKey="value" fill="var(--status-fail)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Root Causes */}
        <div className="card">
          <h2 className="font-semibold mb-4">Root Causes</h2>
          <div className="flex flex-col gap-2">
            {Object.entries(analytics.root_cause_counts).length === 0 && <p className="text-muted">No root causes identified.</p>}
            {Object.entries(analytics.root_cause_counts).map(([name, count]) => (
              <div key={name} className="flex justify-between items-center p-3 bg-slate-800 rounded">
                <span className="font-medium text-sm">{name}</span>
                <span className="badge badge-fail">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
