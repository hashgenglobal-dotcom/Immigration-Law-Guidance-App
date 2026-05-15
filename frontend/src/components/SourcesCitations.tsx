interface Source {
  title: string
  citation: string
  url: string
  type: 'regulation' | 'statute' | 'case' | 'guidance'
}

interface SourcesProps {
  sources: Source[]
}

export default function SourcesCitations({ sources }: SourcesProps) {
  if (!sources || sources.length === 0) {
    return null
  }

  const getTypeLabel = (type: Source['type']) => {
    const labels = {
      regulation: 'Regulation',
      statute: 'Statute',
      case: 'Case law',
      guidance: 'Agency guidance',
    }
    return labels[type] || 'Source'
  }

  return (
    <div className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
      <h3 className="text-lg font-semibold tracking-tight text-forest-900">Official sources</h3>
      <ul className="mt-5 space-y-4">
        {sources.map((source, index) => (
          <li key={index} className="rounded-xl border border-sage-200 bg-cream-100/80 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-forest-900">{source.title}</p>
                <p className="mt-1 text-xs text-sage-800">
                  {getTypeLabel(source.type)} · {source.citation}
                </p>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex shrink-0 items-center justify-center rounded-lg bg-sage-500 px-3 py-2 text-sm font-semibold text-cream-50 shadow-sm transition hover:bg-sage-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-50"
              >
                View source
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
