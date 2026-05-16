import { cn } from '@/lib/cn'

export type RiskLevel = 'low' | 'medium' | 'high'

const levelClass: Record<RiskLevel, string> = {
  low: 'risk-badge-low',
  medium: 'risk-badge-medium',
  high: 'risk-badge-high',
}

export function RiskBadge({
  level,
  className,
  label,
}: {
  level: RiskLevel
  className?: string
  /** Override display text (e.g. "high risk") */
  label?: string
}) {
  return (
    <span className={cn('risk-badge', levelClass[level], className)}>
      {label ?? level}
    </span>
  )
}
