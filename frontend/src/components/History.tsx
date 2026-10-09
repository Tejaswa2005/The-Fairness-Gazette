import type { Verdict } from '../types'

interface HistoryProps {
  verdicts: Verdict[]
  loading: boolean
  error: string | null
  onRefresh: () => void
}

export function History({ verdicts, loading, error, onRefresh }: HistoryProps) {
  return (
    <section className="paper-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="newspaper-kicker mb-2">The Archives</p>
          <h2 className="text-2xl uppercase tracking-wide">Back Issues</h2>
        </div>
        <button type="button" className="action-button" onClick={onRefresh} disabled={loading}>
          Refresh Archive
        </button>
      </div>

      <div className="rule-thin" />

      {loading ? (
        <div className="mt-4 flex items-center gap-3 text-sm uppercase tracking-[0.2em] text-black/65">
          <span className="inline-flex h-4 w-4 animate-spin rounded-full border-2 border-black/25 border-t-[#7b241c]" />
          Retrieving back issues...
        </div>
      ) : null}

      {error ? <p role="alert" className="mt-4 border-l-4 border-[#7b241c] pl-3 text-sm text-[#7b241c]">{error}</p> : null}

      <div className="back-issue mt-4 space-y-4">
        {verdicts.length > 0 ? (
          verdicts.map((verdict) => (
            <article key={verdict.id} className="archive-item">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-black/55">Issue #{verdict.id}</p>
                  <h3 className="mt-1 text-xl uppercase tracking-wide">{verdict.dataset_name}</h3>
                  <p className="mt-1 text-sm text-black/70">Sensitive feature: {verdict.sensitive_feature}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-black">{verdict.fairness_score.toFixed(1)}</p>
                  <p className="uppercase tracking-[0.18em] text-black/75">{verdict.verdict}</p>
                </div>
              </div>
              <p className="mt-3 line-clamp-3 text-sm leading-7 italic text-black/82">{verdict.editor_note}</p>
              <p className="mt-2 text-xs uppercase tracking-[0.22em] text-black/55">Published {new Date(verdict.created_at).toLocaleString()}</p>
            </article>
          ))
        ) : (
          <p className="text-sm text-black/70">No saved verdicts yet.</p>
        )}
      </div>
    </section>
  )
}