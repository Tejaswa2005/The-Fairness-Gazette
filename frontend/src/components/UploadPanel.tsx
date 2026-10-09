import type { ChangeEvent } from 'react'
import type { UploadResponse } from '../types'

interface UploadPanelProps {
  selectedFile: File | null
  uploadPreview: UploadResponse | null
  sensitiveFeature: string
  targetColumn: string
  error: string | null
  loading: boolean
  onFileChange: (file: File | null) => void
  onSensitiveFeatureChange: (value: string) => void
  onTargetColumnChange: (value: string) => void
  onAnalyzeFile: () => void
  onRunAudit: () => void
  onTrySampleCase: () => void
}

export function UploadPanel(props: UploadPanelProps) {
  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    props.onFileChange(file)
  }

  const columns = props.uploadPreview?.columns ?? []

  return (
    <section className="paper-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="newspaper-kicker mb-2">Submit a Case</p>
          <h2 className="text-2xl md:text-3xl uppercase tracking-wide">The Docket</h2>
        </div>
        <span className="badge-pill">Case Intake</span>
      </div>

      <div className="rule-thick" />

      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-4">
          <label className="block">
            <span className="mb-2 block text-xs uppercase tracking-[0.3em] text-black/70">Upload dataset</span>
            <input
              className="block w-full border border-black/25 bg-[#fffdf8] px-4 py-3 text-sm"
              type="file"
              accept=".csv,.xlsx,.xls,.json"
              onChange={handleInputChange}
            />
          </label>

          <div className="flex flex-wrap gap-3">
            <button type="button" className="action-button" onClick={props.onAnalyzeFile} disabled={!props.selectedFile || props.loading}>
              Detect Columns
            </button>
            <button type="button" className="action-button" onClick={props.onTrySampleCase} disabled={props.loading}>
              Try a Sample Case
            </button>
            <button
              type="button"
              className="action-button action-button--accent"
              onClick={props.onRunAudit}
              disabled={!props.selectedFile || !props.sensitiveFeature || props.loading}
            >
              Run Audit
            </button>
          </div>

          {props.error ? <p role="alert" className="border-l-4 border-[#7b241c] pl-3 text-sm text-[#7b241c]">{props.error}</p> : null}
        </div>

        <div className="space-y-3 border-l border-black/15 pl-0 lg:border-l lg:pl-4">
          <div className="space-y-1 text-sm">
            <p className="uppercase tracking-[0.22em] text-black/65">Detected file</p>
            <p className="text-base font-semibold">{props.uploadPreview?.dataset_name ?? props.selectedFile?.name ?? 'Awaiting submission'}</p>
            <p>Rows: {props.uploadPreview?.row_count ?? '—'}</p>
            <p>Type: {props.uploadPreview?.file_type ?? '—'}</p>
          </div>

          <label className="block">
            <span className="mb-2 block text-xs uppercase tracking-[0.3em] text-black/70">Sensitive feature</span>
            <select
              className="w-full border border-black/25 bg-[#fffdf8] px-3 py-2"
              value={props.sensitiveFeature}
              onChange={(event) => props.onSensitiveFeatureChange(event.target.value)}
              disabled={!columns.length}
            >
              <option value="">Select a column</option>
              {columns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-xs uppercase tracking-[0.3em] text-black/70">Target column</span>
            <input
              className="w-full border border-black/25 bg-[#fffdf8] px-3 py-2"
              value={props.targetColumn}
              onChange={(event) => props.onTargetColumnChange(event.target.value)}
            />
          </label>

          {props.uploadPreview ? (
            <div className="rounded border border-black/15 bg-white/60 p-3 text-sm">
              <p className="mb-2 uppercase tracking-[0.2em] text-black/60">Column list</p>
              <div className="flex flex-wrap gap-2">
                {columns.map((column) => (
                  <span key={column} className="badge-pill text-[0.65rem]">
                    {column}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          <p className="text-xs leading-6 text-black/60">
            Accepted formats: CSV, Excel, and JSON. The sample case will load instantly from the newspaper archive.
          </p>
        </div>
      </div>
    </section>
  )
}