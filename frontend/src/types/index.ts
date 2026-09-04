export interface TraceStep {
  id: number;
  trace_id: number;
  step_number: number;
  timestamp: string;
  action_type: string;
  tool_name?: string;
  tool_arguments?: any;
  tool_result?: string;
}

export interface ExecutionTraceResponse {
  id: number;
  test_case_id: number;
  trace_identifier: string;
  final_response?: string;
  final_state?: Record<string, any>;
  metadata?: Record<string, any>;
  steps: TraceStep[];
}

export interface OperationEvaluation {
  operation: string;
  requirement: string;
  satisfied: boolean;
  evidence?: string;
  reason: string;
  attempt_count: number;
}

export interface EntityEvaluation {
  entity: string;
  required_value: any;
  observed_value?: any;
  match_status: string;
}

export interface ConstraintEvaluation {
  constraint_type: string;
  satisfied: boolean;
  reason: string;
}

export interface TaskSuccessEvaluationResult {
  id?: number;
  trace_id: number;
  task_success: string;
  final_verdict: string;
  overall_reason: string;
  determination_method: string;
  operation_evaluations: OperationEvaluation[];
  entity_evaluations: EntityEvaluation[];
  constraint_evaluations: ConstraintEvaluation[];
}

export interface Claim {
  claim: string;
  supported: boolean;
  evidence?: string;
  reasoning: string;
}

export interface ResponseTruthfulnessHistory {
  id: number;
  trace_id: number;
  task_success_evaluation_id?: number;
  response_truthfulness: string;
  response_outcome_claim: string;
  material_claims: Claim[];
  contradictions: Claim[];
  unsupported_claims: Claim[];
  reasoning_summary: string;
  confidence?: number;
}

export interface ReliabilityVerdictResult {
  id?: number;
  task_success_evaluation_id?: number;
  response_truthfulness_evaluation_id?: number;
  task_outcome: string;
  response_truthfulness: string;
  overall_evaluation_verdict: string;
  reliability_classification: string;
  failure_type?: string;
  determination_method: string;
  summary: string;
}

export interface FailureDiagnosisResult {
  id?: number;
  failure_type: string;
  reliability_classification: string;
  root_cause_category: string;
  determination_method: string;
  summary: string;
  supporting_evidence: string[];
  contributing_signals: string[];
}

export interface EvaluationHistoryResult {
  trace_id: number;
  task_success?: TaskSuccessEvaluationResult;
  response_truthfulness?: ResponseTruthfulnessHistory;
  reliability_verdict?: ReliabilityVerdictResult;
  failure_diagnosis?: FailureDiagnosisResult;
}

export interface ReliabilityAnalyticsResponse {
  total_evaluated_traces: number;
  verdict_counts: Record<string, number>;
  reliability_classification_counts: Record<string, number>;
  failure_type_counts: Record<string, number>;
  root_cause_counts: Record<string, number>;
}

export interface BatchEvaluationRequest {
  trace_ids: number[];
}

export interface TraceEvaluationResult {
  trace_id: number;
  status: string;
  error?: string;
  skipped_reason?: string;
}

export interface BatchEvaluationResponse {
  requested_count: number;
  unique_requested_count: number;
  completed_count: number;
  skipped_count: number;
  failed_count: number;
  results: TraceEvaluationResult[];
}
