import type { ReactNode } from 'react'

type CalloutVariant = 'info' | 'warning' | 'danger' | 'success'

const variantClass: Record<CalloutVariant, string> = {
  info: 'border-sage-200 bg-cream-100 text-forest-900',
  warning: 'border-sage-300 bg-sage-50 text-forest-900',
  danger: 'border-forest-800 bg-forest-900 text-cream-200',
  success: 'border-sage-200 bg-cream-50 text-forest-900',
}

export default function Callout({
  variant,
  title,
  children,
  className = '',
}: {
  variant: CalloutVariant
  title?: string
  children: ReactNode
  className?: string
}) {
  return (
    <div
      role="note"
      className={`rounded-xl border px-4 py-3 text-sm leading-relaxed shadow-sm ${variantClass[variant]} ${className}`}
    >
      {title ? (
        <p className="font-semibold tracking-tight">{title}</p>
      ) : null}
      <div className={title ? 'mt-1' : ''}>{children}</div>
    </div>
  )
}
