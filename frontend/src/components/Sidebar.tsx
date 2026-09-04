import React from 'react';
import { Activity, LayoutDashboard, List, Play } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
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
          className={`nav-item ${activeTab === 'traces' ? 'active' : ''}`}
          onClick={() => setActiveTab('traces')}
        >
          <List size={20} />
          <span>Evaluated Traces</span>
        </div>

        <div 
          className={`nav-item ${activeTab === 'batch' ? 'active' : ''}`}
          onClick={() => setActiveTab('batch')}
        >
          <Play size={20} />
          <span>Batch Evaluation</span>
        </div>
      </nav>
      
      <div className="mt-auto">
        <div className="card text-sm text-muted">
          <p>Phase 12 Demonstration</p>
          <p className="mt-2 text-xs">v1.0.0</p>
        </div>
      </div>
    </div>
  );
};
