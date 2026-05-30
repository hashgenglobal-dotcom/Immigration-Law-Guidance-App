import type { ReactNode } from 'react'

type Props = {
  content: string
}

function renderInline(text: string) {
  const parts = text.split(/(\[[^\]]+\]\([^)]+\))/g)
  return parts.map((part, i) => {
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (linkMatch) {
      return (
        <a
          key={i}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-[var(--bronze)] underline-offset-2 hover:text-[var(--bronze-hover)] hover:underline"
        >
          {linkMatch[1]}
        </a>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export default function ScenarioContent({ content }: Props) {
  const lines = content.split('\n')
  const nodes: ReactNode[] = []
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]
    const trimmed = line.trim()

    if (!trimmed) {
      i += 1
      continue
    }

    if (trimmed.startsWith('## ')) {
      nodes.push(
        <h3
          key={key++}
          className="mt-4 border-b border-[var(--border-light)] pb-1 text-xs font-semibold uppercase tracking-wide text-[var(--bronze)] first:mt-0"
        >
          {trimmed.slice(3)}
        </h3>,
      )
      i += 1
      continue
    }

    if (/^\d+\.\s/.test(trimmed)) {
      const items: string[] = []
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s/, ''))
        i += 1
      }
      nodes.push(
        <ol key={key++} className="list-decimal space-y-2 pl-5">
          {items.map((item, idx) => (
            <li key={idx} className="pl-1 text-[var(--text-secondary)]">
              {renderInline(item)}
            </li>
          ))}
        </ol>,
      )
      continue
    }

    if (trimmed.startsWith('- ')) {
      const items: string[] = []
      while (i < lines.length && lines[i].trim().startsWith('- ')) {
        items.push(lines[i].trim().slice(2))
        i += 1
      }
      nodes.push(
        <ul key={key++} className="list-disc space-y-1 pl-5">
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item)}</li>
          ))}
        </ul>,
      )
      continue
    }

    const paragraphLines: string[] = [trimmed]
    i += 1
    while (i < lines.length) {
      const next = lines[i].trim()
      if (!next || next.startsWith('## ') || /^\d+\.\s/.test(next) || next.startsWith('- ')) {
        break
      }
      paragraphLines.push(next)
      i += 1
    }

    nodes.push(
      <p key={key++} className="text-[var(--text-secondary)]">
        {renderInline(paragraphLines.join(' '))}
      </p>,
    )
  }

  return <div className="space-y-3 text-sm leading-relaxed">{nodes}</div>
}
