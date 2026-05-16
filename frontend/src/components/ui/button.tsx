import Link from 'next/link'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

type Variant = 'primary' | 'secondary' | 'ghost' | 'outline-dark' | 'outline-light'
type Size = 'sm' | 'md' | 'lg'

const variantClass: Record<Variant, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost: 'btn-ghost',
  'outline-dark': 'btn-outline-dark',
  'outline-light': 'btn-outline-light',
}

const sizeClass: Record<Size, string> = {
  sm: 'btn-sm',
  md: 'btn-md',
  lg: 'btn-lg',
}

type ButtonProps = {
  variant?: Variant
  size?: Size
  className?: string
  children: ReactNode
  href?: string
} & ButtonHTMLAttributes<HTMLButtonElement>

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  href,
  disabled,
  type = 'button',
  ...rest
}: ButtonProps) {
  const classes = cn(variantClass[variant], sizeClass[size], className)

  if (href) {
    return (
      <Link href={href} className={cn(classes, disabled && 'pointer-events-none opacity-50')} aria-disabled={disabled}>
        <span className="btn-inner">{children}</span>
      </Link>
    )
  }

  return (
    <button type={type} disabled={disabled} className={classes} {...rest}>
      <span className="btn-inner">{children}</span>
    </button>
  )
}
