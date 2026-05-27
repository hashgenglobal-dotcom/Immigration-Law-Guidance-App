import { CheckCircle, ExternalLink, FileText } from 'lucide-react'
import { useState } from 'react'
import type { StructuredResultResponse } from '../../lib/api'

type Props = {
  result: StructuredResultResponse
}

export default function StructuredResultCard({ result }: Props) {
  const [citationsOpen, setCitationsOpen] = useState(false)

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4">
        <div className="border-l-4 border-indigo-500 pl-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
            Short answer
          </div>
          <p className="mt-1 text-sm leading-6 text-slate-800">{result.short_answer}</p>
        </div>
      </div>

      {result.eligibility_checklist.length > 0 ? (
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h4 className="text-sm font-semibold text-slate-900">Eligibility checklist</h4>
          <ul className="mt-3 space-y-2">
            {result.eligibility_checklist.map((item, idx) => (
              <li key={`${idx}-${item}`} className="flex items-start gap-2 text-sm text-slate-700">
                <CheckCircle size={16} className="mt-0.5 shrink-0 text-emerald-600" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {result.next_steps.length > 0 ? (
        <section className="rounded-xl border border-slate-200 bg-white p-4">
          <h4 className="text-sm font-semibold text-slate-900">Next steps</h4>
          <ol className="mt-3 space-y-3">
            {result.next_steps.map((step, idx) => (
              <li key={`${idx}-${step}`} className="flex gap-3">
                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                  {idx + 1}
                </div>
                <p className="pt-0.5 text-sm leading-6 text-slate-700">{step}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <section className="rounded-xl border border-slate-200 bg-white p-4">
        <button
          type="button"
          className="flex w-full items-center justify-between text-left"
          onClick={() => setCitationsOpen((v) => !v)}
        >
          <span className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <FileText size={15} />
            Official Legal References
          </span>
          <span className="text-xs font-medium text-slate-500">
            {citationsOpen ? 'Hide' : 'Show'} ({result.citations.length})
          </span>
        </button>

        {citationsOpen ? (
          result.citations.length > 0 ? (
            <div className="mt-3 space-y-3">
              {result.citations.map((citation, idx) => (
                <article key={`${idx}-${citation.title}`} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <h5 className="text-sm font-semibold text-slate-900">{citation.title}</h5>
                    {citation.url ? (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-indigo-700 hover:text-indigo-900"
                      >
                        Source
                        <ExternalLink size={12} />
                      </a>
                    ) : null}
                  </div>
                  <blockquote className="mt-2 rounded-md bg-slate-100 p-2 text-xs italic leading-5 text-slate-700">
                    {citation.snippet}
                  </blockquote>
                </article>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-500">No citations returned for this answer.</p>
          )
        ) : null}
      </section>

      <p className="text-xs italic text-slate-500">{result.disclaimer}</p>
    </div>
  )
}

