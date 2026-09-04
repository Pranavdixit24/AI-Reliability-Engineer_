import React, { useEffect, useState } from 'react';
import { ArrowLeft, CheckCircle, XCircle, AlertCircle, HelpCircle, User, Bot, PlayCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import type { EvaluationHistoryResult, ExecutionTraceResponse } from '../types';

interface TraceDetailProps {
  traceId: number;
  onBack: () => void;
}

const getStatusBadge = (status: string) => {
  const norm = status?.toUpperCase() || 'UNKNOWN';
  if (['SUCCESS', 'TRUTHFUL', 'PASS', 'RELIABLE_SUCCESS'].includes(norm)) {
    return <span className={`badge badge-pass`}>{norm}</span>;
  }
  if (['FAILURE', 'UNTRUTHFUL', 'FAIL', 'HONEST_FAILURE', 'FALSE_SUCCESS', 'FALSE_FAILURE', 'TASK_EXECUTION_FAILURE', 'ERROR'].includes(norm)) {
    return <span className={`badge badge-fail`}>{norm}</span>;
  }
  return <span className={`badge badge-unknown`}>{norm}</span>;
};

export const TraceDetail: React.FC<TraceDetailProps> = ({ traceId, onBack }) => {
  const [history, setHistory] = useState<EvaluationHistoryResult | null>(null);
  
  const formatActionType = (action: string) => {
    if (!action) return 'Unknown';
    return action.split('_').map(w => w.charAt(0) + w.slice(1).toLowerCase()).join(' ');
  };
  const [trace, setTrace] = useState<ExecutionTraceResponse | null>(null);
  const [testCase, setTestCase] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [traceId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      const traceData = await apiClient.getTrace(traceId);
      setTrace(traceData);
      
      if (traceData.test_case_id) {
         const tcData = await apiClient.getTestCase(traceData.test_case_id);
         setTestCase(tcData);
      }
      
      try {
        const histData = await apiClient.getTraceEvaluationHistory(traceId);
        setHistory(histData);
      } catch (err: any) {
        if (err.message.includes('Not Found') || err.message.includes('not found')) {
           setHistory({ trace_id: traceId });
        } else {
           throw err;
        }
      }
      
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load trace details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-12 text-center">Loading trace narrative...</div>;
  if (error) return <div className="alert-warning"><AlertCircle /> {error}</div>;

  const isEvaluated = history?.reliability_verdict != null;

  return (
    <div className="pb-12">
      <div className="flex items-center gap-4 mb-6">
        <button className="btn" style={{ padding: '0.4rem', backgroundColor: 'var(--panel-border)' }} onClick={onBack}>
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold">Trace #{traceId}</h1>
        {isEvaluated ? (
          <span className="badge badge-pass ml-auto">Evaluated</span>
        ) : (
          <span className="badge badge-unknown ml-auto">Not Evaluated</span>
        )}
      </div>

      {/* SECTION 1: WHAT WAS REQUESTED */}
      <section className="mb-8">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2 uppercase tracking-wider text-accent border-b border-slate-700 pb-2">
          <User size={20} /> Test Case Specification
        </h2>
        {testCase ? (
          <div className="card bg-slate-800/50">
            <div className="mb-4">
              <span className="text-sm text-muted uppercase">Expected Intent</span>
              <div className="font-medium text-lg mt-1">{testCase.success_specification?.required_intent || 'N/A'}</div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-muted uppercase block mb-2">Required Entity</span>
                {Object.keys(testCase.success_specification?.required_entities || {}).length > 0 ? (
                  <ul className="list-disc pl-5">
                    {Object.entries(testCase.success_specification.required_entities).map(([k, v]) => (
                      <li key={k}><span className="font-mono text-sm">{k}</span> = {typeof v === 'string' ? v : JSON.stringify(v)}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-muted text-sm">None required</span>
                )}
              </div>
              
              <div>
                <span className="text-sm text-muted uppercase block mb-2">Success Requirement</span>
                {testCase.success_specification?.required_operations?.length > 0 ? (
                  <ul className="list-disc pl-5">
                    {testCase.success_specification.required_operations.map((op: any, i: number) => (
                      <li key={i}><span className="font-mono text-sm">{op.operation}</span> {op.must_succeed ? '(must succeed)' : ''}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-muted text-sm">None required</span>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-muted">No test case context found.</div>
        )}
      </section>

      {/* SECTION 2 & 3: WHAT THE AGENT DID & ACTUALLY HAPPENED */}
      <section className="mb-8">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2 uppercase tracking-wider text-accent border-b border-slate-700 pb-2">
          <PlayCircle size={20} /> Observed Agent Execution
        </h2>
        
        {trace?.steps?.length ? (
          <div className="flex flex-col gap-4">
            {trace.steps.map((step) => (
              <div key={step.id} className="card phase-card relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-accent/50" />
                
                <div className="flex justify-between items-start mb-2">
                  <span className="font-bold text-slate-300">Step {step.step_number} &mdash; {formatActionType(step.action_type)}</span>
                  {step.status && getStatusBadge(step.status)}
                </div>
                
                {step.action_type === 'INTENT_RECOGNITION' && step.intent && (
                  <div className="mt-2 text-sm">
                    <span className="text-muted">Recognized Intent: </span>
                    <span className="font-mono text-emerald-400">{step.intent}</span>
                  </div>
                )}
                
                {step.action_type === 'ENTITY_EXTRACTION' && step.tool_arguments && (
                  <div className="mt-2 text-sm">
                    <span className="text-muted block mb-1">Extracted Entity:</span>
                    {Object.entries(step.tool_arguments).map(([k, v]) => (
                      <div key={k} className="font-mono text-blue-300">
                        {k} = {typeof v === 'string' ? v : JSON.stringify(v)}
                      </div>
                    ))}
                  </div>
                )}
                
                {step.action_type === 'TOOL_CALL' && step.tool_name && (
                  <div className="mt-2">
                    <div className="text-sm text-muted mb-1">Tool:</div>
                    <div className="bg-slate-900 p-2 rounded font-mono text-sm text-blue-300">
                      {step.tool_name}({JSON.stringify(step.tool_arguments || {})})
                    </div>
                  </div>
                )}
                
                {step.action_type === 'TOOL_RESULT' && step.tool_name && (
                  <div className="mt-2">
                    <div className="text-sm text-muted mb-1">Tool: <span className="text-slate-300 font-mono">{step.tool_name}</span></div>
                    {step.tool_result && (
                      <div className="mt-2">
                        <div className="text-sm text-muted mb-1">Result / Error:</div>
                        <div className="bg-slate-900 p-2 rounded font-mono text-sm text-slate-300 whitespace-pre-wrap">
                          {step.tool_result}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {step.action_type === 'FINAL_RESPONSE' && (
                  <div className="mt-2">
                    <div className="bg-slate-900 p-2 rounded font-mono text-sm text-slate-300 whitespace-pre-wrap">
                      {step.tool_result || step.tool_arguments?.response || "No response text captured."}
                    </div>
                  </div>
                )}
                
                {step.error_information && (
                  <div className="mt-2 text-red-400 text-sm bg-red-900/20 p-2 rounded border border-red-900/50">
                    <AlertCircle size={14} className="inline mr-1" /> {step.error_information}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-muted">No execution steps recorded.</div>
        )}
      </section>

      {/* SECTION 4: WHAT THE AGENT SAID */}
      <section className="mb-12">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2 uppercase tracking-wider text-accent border-b border-slate-700 pb-2">
          <Bot size={20} /> Agent Final Response
        </h2>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 text-lg">
          {trace?.final_response ? `"${trace.final_response}"` : <span className="text-muted italic">No final response provided.</span>}
        </div>
      </section>

      {/* SECTION 5: HOW THE RELIABILITY SYSTEM JUDGED IT */}
      <section>
        <h2 className="text-lg font-bold mb-6 flex items-center gap-2 uppercase tracking-wider text-accent border-b border-slate-700 pb-2">
          Reliability Evaluation Lifecycle
        </h2>
        
        {!isEvaluated ? (
          <div className="card bg-slate-800/50 text-center py-12">
            <HelpCircle size={48} className="mx-auto text-slate-600 mb-4" />
            <h3 className="text-xl font-bold text-slate-400">Not Evaluated Yet</h3>
            <p className="text-muted mt-2 max-w-md mx-auto">This trace has not completed the Reliability Evaluation lifecycle (Phases 5-8).</p>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            <div className="card phase-card">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                Task Success Evaluation (Phase 5)
              </h3>
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
                          <h4 className="font-semibold text-sm mb-2">Operation Evaluations</h4>
                          <div className="flex flex-col gap-2">
                              {history.task_success.operation_evaluations.map((op, i) => (
                                  <div key={i} className="flex justify-between p-2 bg-slate-900 rounded text-sm">
                                      <span>{op.operation} ({op.requirement})</span>
                                      <span>{op.satisfied ? <CheckCircle size={16} className="text-emerald-500" /> : <XCircle size={16} className="text-red-500" />}</span>
                                  </div>
                              ))}
                          </div>
                      </div>
                  )}
                </div>
              ) : (
                <div className="text-muted flex items-center gap-2"><HelpCircle size={16}/> Not evaluated</div>
              )}
            </div>

            <div className="card phase-card">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                Response Truthfulness (Phase 6)
              </h3>
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
                <div className="text-muted flex items-center gap-2"><HelpCircle size={16}/> Not evaluated</div>
              )}
            </div>

            <div className="card phase-card">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                Reliability Verdict (Phase 7)
              </h3>
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
                <div className="text-muted flex items-center gap-2"><HelpCircle size={16}/> Not evaluated</div>
              )}
            </div>

            <div className="card phase-card">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                Failure Diagnosis (Phase 8)
              </h3>
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
                          <h4 className="font-semibold text-sm mb-2">Supporting Evidence</h4>
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
                     : <><HelpCircle size={16}/> Not evaluated</>}
                </div>
              )}
            </div>
          </div>
        )}
      </section>

    </div>
  );
};
