import { useEffect, useMemo, useState } from 'react'
import { AuditResultPanel } from './components/AuditResult'
import { History } from './components/History'
import { UploadPanel } from './components/UploadPanel'
import { fileAppeal, formatApiError, getVerdicts, isBackendUnavailableError, runAudit, uploadFile } from './services/api'
import type { AppealResponse, AuditResult, UploadResponse, Verdict } from './types'

export default function App() {
	const [selectedFile, setSelectedFile] = useState<File | null>(null)
	const [uploadPreview, setUploadPreview] = useState<UploadResponse | null>(null)
	const [sensitiveFeature, setSensitiveFeature] = useState('')
	const [targetColumn, setTargetColumn] = useState('approved')
	const [auditResult, setAuditResult] = useState<AuditResult | null>(null)
	const [appealResult, setAppealResult] = useState<AppealResponse | null>(null)
	const [verdicts, setVerdicts] = useState<Verdict[]>([])
	const [loading, setLoading] = useState(false)
	const [auditing, setAuditing] = useState(false)
	const [historyLoading, setHistoryLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [historyError, setHistoryError] = useState<string | null>(null)

	const mastheadDate = useMemo(
		() =>
			new Intl.DateTimeFormat('en-US', {
				weekday: 'long',
				year: 'numeric',
				month: 'long',
				day: 'numeric',
			}).format(new Date()),
		[],
	)

	const issueLabel = useMemo(() => {
		if (auditResult) {
			return `Case No. ${String(auditResult.id).padStart(3, '0')}`
		}

		if (verdicts[0]) {
			return `Case No. ${String(verdicts[0].id).padStart(3, '0')}`
		}

		return 'Case No. XXX'
	}, [auditResult, verdicts])

	useEffect(() => {
		void loadHistory()
	}, [])

	async function loadHistory() {
		try {
			setHistoryLoading(true)
			setHistoryError(null)
			const savedVerdicts = await getVerdicts()
			setVerdicts(savedVerdicts)
		} catch (unknownError) {
			setHistoryError(formatApiError(unknownError))
		} finally {
			setHistoryLoading(false)
		}
	}

	async function runSampleCase() {
		try {
			setLoading(true)
			setError(null)
			setHistoryError(null)
			const response = await fetch('/sample-case.csv')
			if (!response.ok) {
				throw new Error('The sample case could not be loaded from the app bundle.')
			}

			const blob = await response.blob()
			const sampleFile = new File([blob], 'sample-case.csv', { type: 'text/csv' })
			setSelectedFile(sampleFile)

			const uploadResponse = await uploadFile(sampleFile)
			setUploadPreview(uploadResponse)
			const defaultSensitive = uploadResponse.columns.includes('gender') ? 'gender' : uploadResponse.columns[0] ?? ''
			setSensitiveFeature(defaultSensitive)
			setTargetColumn(uploadResponse.columns.includes('approved') ? 'approved' : targetColumn)

			if (defaultSensitive) {
				setAuditing(true)
				const result = await runAudit(sampleFile, {
					dataset_name: uploadResponse.dataset_name,
					sensitive_feature: defaultSensitive,
					target_column: uploadResponse.columns.includes('approved') ? 'approved' : targetColumn,
				})
				setAuditResult(result)
				setAppealResult(null)
				await loadHistory()
			}
		} catch (unknownError) {
			setError(
				isBackendUnavailableError(unknownError)
					? 'The newsroom cannot reach the court right now. Please start the backend and try the sample case again.'
					: formatApiError(unknownError),
			)
		} finally {
			setAuditing(false)
			setLoading(false)
		}
	}

	async function handleAnalyzeFile() {
		if (!selectedFile) {
			setError('Choose a CSV, Excel, or JSON file first, or use the sample case edition.')
			return
		}

		try {
			setLoading(true)
			setError(null)
			setAuditResult(null)
			setAppealResult(null)
			const uploadResponse = await uploadFile(selectedFile)
			setUploadPreview(uploadResponse)
			setSensitiveFeature((current) => current || uploadResponse.columns[0] || '')
			setTargetColumn('approved')
		} catch (unknownError) {
			setError(formatApiError(unknownError))
		} finally {
			setLoading(false)
		}
	}

	async function handleRunAudit() {
		if (!selectedFile || !sensitiveFeature) {
			setError('Upload a file and select a sensitive feature before taking the case to trial.')
			return
		}

		try {
			setAuditing(true)
			setError(null)
			const result = await runAudit(selectedFile, {
				dataset_name: uploadPreview?.dataset_name,
				sensitive_feature: sensitiveFeature,
				target_column: targetColumn,
			})
			setAuditResult(result)
			setAppealResult(null)
			await loadHistory()
		} catch (unknownError) {
			setError(
				isBackendUnavailableError(unknownError)
					? 'The backend is unavailable. Please check the court server and try again.'
					: formatApiError(unknownError),
			)
		} finally {
			setAuditing(false)
		}
	}

	async function handleRunAppeal() {
		if (!selectedFile || !sensitiveFeature) {
			setError('Upload a file and select a sensitive feature before filing an appeal.')
			return
		}

		try {
			setAuditing(true)
			setError(null)
			const result = await fileAppeal(selectedFile, {
				dataset_name: uploadPreview?.dataset_name,
				sensitive_feature: sensitiveFeature,
				target_column: targetColumn,
			})
			setAppealResult(result)
		} catch (unknownError) {
			setError(
				isBackendUnavailableError(unknownError)
					? 'The backend is unavailable. The appeal desk is waiting for the court to reopen.'
					: formatApiError(unknownError),
			)
		} finally {
			setAuditing(false)
		}
	}

	function handleDownloadVerdict() {
		window.print()
	}

	return (
		<div className="newsprint-shell">
			<main className="newspaper-page space-y-5">
				<header className="paper-panel text-center">
					<div className="flex flex-wrap items-center justify-between gap-3 text-xs uppercase tracking-[0.25em] text-black/65">
						<span>{mastheadDate}</span>
						<span>{issueLabel}</span>
					</div>
					<div className="rule-thick" />
					<h1 className="masthead-title">The Fairness Gazette</h1>
					<p className="masthead-motto">All Models Are Equal Before the Data</p>
					<div className="rule-thick" />
					<p className="mx-auto max-w-4xl text-sm uppercase tracking-[0.22em] text-black/70 md:text-base">
						A judicial newspaper for machine-learning verdicts, fairness evidence, and the public record.
					</p>
				</header>

				<div className="newspaper-grid">
					<div className="space-y-5">
						<UploadPanel
							selectedFile={selectedFile}
							uploadPreview={uploadPreview}
							sensitiveFeature={sensitiveFeature}
							targetColumn={targetColumn}
							error={error}
							loading={loading}
							onTrySampleCase={runSampleCase}
							onFileChange={setSelectedFile}
							onSensitiveFeatureChange={setSensitiveFeature}
							onTargetColumnChange={setTargetColumn}
							onAnalyzeFile={handleAnalyzeFile}
							onRunAudit={handleRunAudit}
						/>

						<History verdicts={verdicts} loading={historyLoading} error={historyError} onRefresh={loadHistory} />
					</div>

					<div className="space-y-5">
						<AuditResultPanel
							auditResult={auditResult}
							appealResult={appealResult}
							onRunAppeal={handleRunAppeal}
							onDownloadVerdict={handleDownloadVerdict}
							loading={auditing}
						/>
					</div>
				</div>
			</main>
		</div>
	)
}
