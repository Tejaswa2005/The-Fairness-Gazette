import type { AppealResponse, AuditResult, FairnessMetrics } from '../types'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface AuditResultProps {
  auditResult: AuditResult | null
  appealResult: AppealResponse | null
  onRunAppeal: () => void
  onDownloadVerdict: () => void
  loading: boolean
}

function getGroupNames(metrics: FairnessMetrics | Record<string, unknown> | null): Array<[string, number]> {
  if (!metrics || typeof metrics !== 'object' || !('selection_rate_by_group' in metrics)) {
    return []
  }

  const selectionRateByGroup = (metrics as FairnessMetrics).selection_rate_by_group
  return Object.entries(selectionRateByGroup)
}

function buildHeadline(auditResult: AuditResult | null): string {
  if (!auditResult) {
    return 'The Bench Awaits Its First Case'
  }

  const score = auditResult.fairness_score
  const verdict = auditResult.verdict === 'GUILTY' ? 'GUILTY OF BIAS' : 'ACQUITTED OF SYSTEMIC BIAS'

  if (score < 40) {
    return `MODEL FOUND ${verdict}`
  }

  if (score < 70) {
    return `MODEL ${verdict} WITH CAUTION`
  }

  return `MODEL ${verdict}`
}

function buildSubhead(auditResult: AuditResult | null): string {
  if (!auditResult) {
    return 'File a dataset, select a sensitive feature, and bring the model before the court.'
  }

  const entries = getGroupNames(auditResult.metrics)
  if (entries.length < 2) {
    return 'The evidence has been entered into the record and the verdict has been rendered.'
  }

  const sorted = [...entries].sort((left, right) => left[1] - right[1])
  const low = sorted[0]
  const high = sorted[sorted.length - 1]
  const ratio = high[1] > 0 ? high[1] / Math.max(low[1], 0.0001) : 0

  if (ratio >= 2) {
    return `${low[0]} applicants are selected at roughly half the rate of ${high[0]} applicants.`
  }

  return `${low[0]} and ${high[0]} remain the widest-separated groups in the current record.`
}

function buildChartData(auditResult: AuditResult | null) {
  const entries = getGroupNames(auditResult?.metrics ?? null)
  if (entries.length === 0) {
    return []
  }

  const maximum = Math.max(...entries.map((entry) => entry[1]))
  const minimum = Math.min(...entries.map((entry) => entry[1]))

  return entries.map(([name, value]) => ({
    name,
    rate: value,
    accent: value === maximum || value === minimum ? '#7b241c' : '#111111',
  }))
}

function MetricLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-black/10 py-2 text-sm">
      <span className="uppercase tracking-[0.22em] text-black/60">{label}</span>
      <span className="font-semibold text-black">{value}</span>
    </div>
  )
}

export function AuditResultPanel({ auditResult, appealResult, onRunAppeal, onDownloadVerdict, loading }: AuditResultProps) {
  const chartData = buildChartData(auditResult)

  return (
    <section className="space-y-4">
      <article className="paper-panel">
        <p className="newspaper-kicker mb-2">Front Page Verdict</p>
        <div className="rule-thin" />

        <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr] lg:items-start">
          <div>
            <h2 className="newspaper-headline headline-accent">{buildHeadline(auditResult)}</h2>
            <p className="mt-4 max-w-4xl text-base leading-8 tracking-[0.01em] text-black/85">{buildSubhead(auditResult)}</p>
          </div>

          <div className="flex flex-col items-start gap-3 lg:items-end">
            <button type="button" className="action-button action-button--accent" onClick={onRunAppeal} disabled={!auditResult}>
              File an Appeal
            </button>
            <button type="button" className="action-button" onClick={onDownloadVerdict} disabled={!auditResult}>
              Download the Verdict
            </button>
          </div>
        </div>

        {loading ? (
          <div className="mt-4 flex items-center gap-3 border-t border-black/10 pt-4 text-sm uppercase tracking-[0.2em] text-black/65">
            <span className="inline-flex h-5 w-5 animate-spin rounded-full border-2 border-black/25 border-t-[#7b241c]" />
            The press room is setting the type...
          </div>
        ) : null}
      </article>

      <div className="issue-grid">
        <article className="paper-panel">
          <p className="newspaper-kicker mb-2">The Evidence</p>
          <div className="rule-thin" />

          {auditResult && chartData.length > 0 ? (
            <div className="mt-4 h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 12, right: 20, bottom: 12, left: 24 }}>
                  <CartesianGrid strokeDasharray="4 4" stroke="rgba(0,0,0,0.12)" />
                  <XAxis type="number" stroke="#111111" tick={{ fill: '#111111', fontFamily: 'Merriweather, Georgia, serif', fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="#111111"
                    tick={{ fill: '#111111', fontFamily: 'Merriweather, Georgia, serif', fontSize: 12 }}
                    width={110}
                  />
                  <Tooltip
                    cursor={{ fill: 'rgba(123, 36, 28, 0.08)' }}
                    contentStyle={{ background: '#f8f3ea', border: '1px solid rgba(0,0,0,0.2)', borderRadius: 4 }}
                  />
                  <Bar dataKey="rate" barSize={22} radius={[0, 4, 4, 0]}>
                    {chartData.map((entry) => (
                      <Cell key={entry.name} fill={entry.accent} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="mt-4 text-sm text-black/70">No evidence chart is available until an audit is run.</p>
          )}

          {auditResult ? (
            <div className="mt-4 grid gap-2 md:grid-cols-3">
              <MetricLine label="Demographic parity" value={auditResult.metrics.demographic_parity_difference.toFixed(3)} />
              <MetricLine label="Equalized odds" value={auditResult.metrics.equalized_odds_difference.toFixed(3)} />
              <MetricLine label="Selection spread" value={auditResult.metrics.selection_rate_spread.toFixed(3)} />
            </div>
          ) : null}
        </article>

        <article className="paper-panel">
          <p className="newspaper-kicker mb-2">The Ruling</p>
          <div className="rule-thin" />

          {auditResult ? (
            <div className="mt-4 flex flex-col items-center gap-5 text-center">
              <div className="w-full rounded border border-black/15 bg-white/60 p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-black/60">Fairness Score</p>
                <p className="mt-2 text-5xl font-black leading-none">{auditResult.fairness_score.toFixed(1)}<span className="text-2xl">/100</span></p>
                <p className="mt-2 text-lg font-semibold uppercase tracking-[0.18em]">{auditResult.verdict}</p>
              </div>

              <div className="wax-seal">
                <span>
                  <strong>{auditResult.verdict}</strong>
                  <span>Stamped</span>
                </span>
              </div>

              <p className="max-w-sm text-sm uppercase tracking-[0.18em] text-black/65">
                The bench has reviewed the data, weighed the evidence, and entered its finding into the permanent record.
              </p>
            </div>
          ) : (
            <p className="mt-4 text-sm text-black/70">Run an audit to reveal the ruling and the full evidence sheet.</p>
          )}
        </article>
      </div>

      <article className="paper-panel">
        <p className="newspaper-kicker mb-2">Editor&apos;s Note</p>
        <div className="rule-thin" />

        {auditResult ? (
          <div className="prose-columns mt-4 text-[1.02rem] leading-8 italic text-black/88">
            <p className="drop-cap whitespace-pre-line">{auditResult.editor_note}</p>
          </div>
        ) : (
          <p className="mt-4 text-sm text-black/70">The editorial desk will draft its note once the court has spoken.</p>
        )}
      </article>

      {appealResult ? (
        <article className="paper-panel">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="newspaper-kicker mb-2">New Edition</p>
              <h3 className="text-2xl uppercase tracking-wide">Before vs After Appeal</h3>
            </div>
            <span className="badge-pill">Appeal Granted</span>
          </div>
          <div className="rule-thin" />

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="border border-black/15 bg-white/70 p-4">
              <p className="print-only-note mb-2">Before</p>
              <p className="text-3xl font-black">{appealResult.before.fairness_score.toFixed(1)}/100</p>
              <p className="mt-2 uppercase tracking-[0.18em]">{appealResult.before.verdict}</p>
              <p className="mt-4 whitespace-pre-line text-sm leading-7 italic">{appealResult.before.editor_note}</p>
            </div>
            <div className="border border-black/15 bg-white/70 p-4">
              <p className="print-only-note mb-2">After</p>
              <p className="text-3xl font-black">{appealResult.after.fairness_score.toFixed(1)}/100</p>
              <p className="mt-2 uppercase tracking-[0.18em]">{appealResult.after.verdict}</p>
              <p className="mt-4 whitespace-pre-line text-sm leading-7 italic">{appealResult.after.editor_note}</p>
            </div>
          </div>
        </article>
      ) : null}
    </section>
  )
}