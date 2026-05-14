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
      case: 'Case Law',
      guidance: 'Agency Guidance',
    }
    return labels[type] || 'Source'
  }

  return (
    <div className="bg-gray-50 rounded-lg p-6 mt-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Official Sources</h3>
      <ul className="space-y-4">
        {sources.map((source, index) => (
          <li key={index} className="border-l-4 border-primary-600 pl-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{source.title}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {getTypeLabel(source.type)} • {source.citation}
                </p>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-800 text-sm font-medium ml-4"
              >
                View Source →
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
