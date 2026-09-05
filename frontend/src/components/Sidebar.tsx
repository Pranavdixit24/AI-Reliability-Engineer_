import React, { useEffect, useState } from 'react';
import { Activity, LayoutDashboard, List, Play, Database } from 'lucide-react';
import { apiClient } from '../api/client';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const [totalTraces, setTotalTraces] = useState<number | null>(null);
  const [evaluatedTraces, setEvaluatedTraces] = useState<number | null>(null);

  useEffect(() => {
    // Fetch counts for sidebar
    const fetchCounts = async () => {
      try {
        const [allData, evalData] = await Promise.all([
          apiClient.getTracesSummary(0, 1, false),
          apiClient.getTracesSummary(0, 1, true)
        ]);
        setTotalTraces(allData.total);
        setEvaluatedTraces(evalData.total);
      } catch (err) {
        console.error('Failed to fetch counts for sidebar', err);
      }
    };
    fetchCounts();
  }, [activeTab]); // Refresh counts when tab changes (could be after an evaluation)

  return (
    <div className="sidebar">
      <div className="flex items-center gap-2 mb-6">
        <Activity size={24} className="text-accent" style={{ color: 'var(--accent-primary)' }} />
        <h1 className="font-bold text-lg">AI Reliability Eng.</h1>
      </div>

      <nav>
        <div 
          className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </div>
        
        <div 
          className={`nav-item ${activeTab === 'all-traces' ? 'active' : ''}`}
          onClick={() => setActiveTab('all-traces')}
        >
          <Database size={20} />
          <div className="flex flex-col">
            <span>All Traces</span>
            {totalTraces !== null && <span className="text-xs text-muted">{totalTraces} total traces</span>}
          </div>
        </div>
        
        <div 
          className={`nav-item ${activeTab === 'evaluated' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluated')}
        >
          <List size={20} />
          <div className="flex flex-col">
            <span>Evaluated Traces</span>
            {evaluatedTraces !== null && <span className="text-xs text-muted">{evaluatedTraces} evaluated</span>}
          </div>
        </div>

        <div 
          className={`nav-item ${activeTab === 'batch' ? 'active' : ''}`}
          onClick={() => setActiveTab('batch')}
        >
          <Play size={20} />
          <span>Batch Evaluation</span>
        </div>
      </nav>
      

    </div>
  );
};
