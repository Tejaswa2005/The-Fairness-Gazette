import axios, { AxiosError } from 'axios'
import type {
	AppealResponse,
	AuditRequest,
	AuditResult,
	ApiError,
	UploadResponse,
	Verdict,
	VerdictHistoryResponse,
} from '../types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const apiClient = axios.create({
	baseURL: apiBaseUrl,
	timeout: 30000,
})

function getFriendlyError(error: unknown): string {
	if (axios.isAxiosError(error)) {
		const axiosError = error as AxiosError<ApiError>
		if (!axiosError.response) {
			return 'The backend is unavailable right now. Please start the API and try again.'
		}
		return axiosError.response?.data?.detail ?? axiosError.message ?? 'Something went wrong while talking to the API.'
	}

	if (error instanceof Error) {
		return error.message
	}

	return 'Something went wrong while talking to the API.'
}

export function formatApiError(error: unknown): string {
	return getFriendlyError(error)
}

export function isBackendUnavailableError(error: unknown): boolean {
	return axios.isAxiosError(error) && !error.response
}

export async function uploadFile(file: File): Promise<UploadResponse> {
	const formData = new FormData()
	formData.append('file', file)

	const response = await apiClient.post<UploadResponse>('/upload', formData, {
		headers: { 'Content-Type': 'multipart/form-data' },
	})

	return response.data
}

export async function runAudit(file: File, request: AuditRequest): Promise<AuditResult> {
	const formData = new FormData()
	formData.append('file', file)
	formData.append('sensitive_feature', request.sensitive_feature)
	formData.append('target_column', request.target_column ?? 'approved')

	if (request.dataset_name) {
		formData.append('dataset_name', request.dataset_name)
	}

	const response = await apiClient.post<AuditResult>('/audit', formData, {
		headers: { 'Content-Type': 'multipart/form-data' },
	})

	return response.data
}

export async function fileAppeal(file: File, request: AuditRequest): Promise<AppealResponse> {
	const formData = new FormData()
	formData.append('file', file)
	formData.append('sensitive_feature', request.sensitive_feature)
	formData.append('target_column', request.target_column ?? 'approved')

	if (request.dataset_name) {
		formData.append('dataset_name', request.dataset_name)
	}

	const response = await apiClient.post<AppealResponse>('/appeal', formData, {
		headers: { 'Content-Type': 'multipart/form-data' },
	})

	return response.data
}

export async function getVerdicts(): Promise<Verdict[]> {
	const response = await apiClient.get<VerdictHistoryResponse>('/verdicts')
	return response.data.items
}

export async function getVerdict(id: number): Promise<Verdict> {
	const response = await apiClient.get<Verdict>(`/verdicts/${id}`)
	return response.data
}
