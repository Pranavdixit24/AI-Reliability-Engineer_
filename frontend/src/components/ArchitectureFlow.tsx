import React from 'react';
import { Database, FileCode, CheckSquare, Search, FileSignature, AlertTriangle, BarChart3, ArrowDown } from 'lucide-react';

export const ArchitectureFlow: React.FC = () => {
  const steps = [
    { name: 'Synthetic Test Case', icon: <FileCode size={20} />, phase: 'Phase 2' },
    { name: 'Execution Trace Generation', icon: <PlayIcon size={20} />, phase: 'Phase 3' },
    { name: 'Trace Facts Normalization', icon: <Database size={20} />, phase: 'Phase 4' },
    { name: 'Task Success Evaluation', icon: <CheckSquare size={20} />, phase: 'Phase 5', highlight: true },
    { name: 'Response Truthfulness', icon: <Search size={20} />, phase: 'Phase 6', highlight: true },
    { name: 'Reliability Verdict', icon: <FileSignature size={20} />, phase: 'Phase 7', highlight: true },
    { name: 'Failure Diagnosis', icon: <AlertTriangle size={20} />, phase: 'Phase 8', highlight: true },
    { name: 'Reliability Analytics', icon: <BarChart3 size={20} />, phase: 'Phase 10', highlight: true }
  ];

  return (
    <div className="card h-full">
      <h2 className="font-semibold mb-4">Evaluation Pipeline</h2>
      <div className="flex flex-col items-center">
        {steps.map((step, index) => (
          <React.Fragment key={index}>
            <div 
              className={`flex items-center justify-between w-full p-3 rounded border ${
                step.highlight ? 'bg-blue-900 bg-opacity-20 border-blue-500 text-blue-100' : 'bg-slate-800 border-slate-700 text-slate-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={step.highlight ? 'text-blue-400' : 'text-slate-500'}>
                  {step.icon}
                </div>
                <span className="font-medium text-sm">{step.name}</span>
              </div>
              <span className="text-xs opacity-60 font-mono">{step.phase}</span>
            </div>
            {index < steps.length - 1 && (
              <div className="my-1 text-slate-600">
                <ArrowDown size={16} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

const PlayIcon = ({ size }: { size: number }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="5 3 19 12 5 21 5 3"></polygon>
  </svg>
);
