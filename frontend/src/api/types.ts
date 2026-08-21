export type ComparisonOperator =
  | "<"
  | "<="
  | ">"
  | ">="
  | "=="
  | "!="
  | "in"
  | "not_in"

export type ComplianceStatus =
  | "Compliant"
  | "Non-Compliant"
  | "Not Applicable"
  | "Unknown"

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue }

export interface PreCondition {
  target_metric: string
  operator: ComparisonOperator
  threshold_value: JsonValue
}

export interface ExtractedRuleBase {
  id?: string
  control_id: string
  title: string
  target_asset_type: string
  target_metric: string
  operator: ComparisonOperator
  threshold_value: JsonValue
  source_clause: string
  page_number?: number | null
  pre_condition?: PreCondition | null
  is_active?: boolean
}

export interface PolicyExtractionPayload {
  policy_name: string
  rules: ExtractedRuleBase[]
}

export interface PolicyIngestionResponse {
  policy_id: string
  policy_name: string
  rules: ExtractedRuleBase[]
}

export interface PolicyListItem {
  id: string
  name: string
  created_at: string
  rule_count: number
}

export interface EvidenceAsset {
  asset_id: string
  asset_type: string
  metrics: Record<string, JsonValue>
  region?: string
}

export interface EvidencePayload {
  scan_id: string
  environment: string
  assets: EvidenceAsset[]
}

export interface RuleEvaluationResult {
  control_id: string
  target_metric: string
  operator: string
  threshold_value: JsonValue
  actual_value?: JsonValue | null
  status: ComplianceStatus
  audit_reasoning: string
  source_clause?: string | null
}

export interface AssetEvaluationResult {
  asset_id: string
  asset_type: string
  overall_status: ComplianceStatus
  checks: RuleEvaluationResult[]
}

export interface ComplianceScanResponse {
  scan_id: string
  environment: string
  overall_status: ComplianceStatus
  total_assets: number
  compliant_assets_count: number
  non_compliant_assets_count: number
  asset_results: AssetEvaluationResult[]
}

export interface HealthResponse {
  status: string
  service: string
  database: string
  provider: string
}
