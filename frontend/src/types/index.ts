export interface UploadResponse {
	dataset_name: string
	file_type: string
	row_count: number
	columns: string[]
	column_types: Record<string, string>
	preview_rows: Array<Record<string, unknown>>
}

export interface AuditRequest {
	dataset_name?: string
	sensitive_feature: string
	target_column?: string
}

export interface FairnessMetrics {
	demographic_parity_difference: number
	equalized_odds_difference: number
	selection_rate_by_group: Record<string, number>
	selection_rate_spread: number
}

export interface Verdict {
	id: number
	dataset_name: string
	sensitive_feature: string
	fairness_score: number
	verdict: 'GUILTY' | 'ACQUITTED'
	editor_note: string
	metrics: Record<string, unknown>
	created_at: string
}

export interface AuditResult extends Omit<Verdict, 'metrics'> {
	metrics: FairnessMetrics
}

export interface MitigationSnapshot {
	metrics: FairnessMetrics
	fairness_score: number
	verdict: 'GUILTY' | 'ACQUITTED'
	editor_note: string
}

export interface AppealResponse {
	before: MitigationSnapshot
	after: MitigationSnapshot
	improvement: Record<string, number>
}

export interface VerdictHistoryResponse {
	items: Verdict[]
}

export interface ApiError {
	detail: string
}
