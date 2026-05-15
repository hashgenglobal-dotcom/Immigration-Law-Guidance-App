'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import {
  Plus,
  BookOpen,
  Paperclip,
  FileText,
  ChevronDown,
  Check,
  SendHorizontal,
  Scale,
  List,
  MapPin,
  Library,
} from 'lucide-react'

interface AnswerMode {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  badge?: string
}

const answerModes: AnswerMode[] = [
  {
    id: 'citations',
    name: 'Citations first',
    description: 'Lead with official sources you can verify',
    icon: <FileText className="size-4 text-sage-300" />,
    badge: 'Default',
  },
  {
    id: 'plain',
    name: 'Plain language',
    description: 'Simpler wording, still source-backed',
    icon: <BookOpen className="size-4 text-cream-200/90" />,
  },
  {
    id: 'brief',
    name: 'Brief summary',
    description: 'Short overview plus practical next steps',
    icon: <List className="size-4 text-sage-200" />,
  },
]

function ModeSelector({
  selectedId = 'citations',
  onModeChange,
}: {
  selectedId?: string
  onModeChange?: (mode: AnswerMode) => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [selected, setSelected] = useState(
    () => answerModes.find((m) => m.id === selectedId) ?? answerModes[0],
  )

  const handleSelect = (mode: AnswerMode) => {
    setSelected(mode)
    setIsOpen(false)
    onModeChange?.(mode)
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-medium text-sage-300/90 transition-all duration-200 hover:bg-cream-200/10 hover:text-cream-50 active:scale-95"
      >
        {selected.icon}
        <span className="max-w-[7rem] truncate sm:max-w-none">{selected.name}</span>
        <ChevronDown className={`size-3.5 shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen ? (
        <>
          <button type="button" className="fixed inset-0 z-40 cursor-default bg-transparent" aria-label="Close menu" onClick={() => setIsOpen(false)} />
          <div className="absolute bottom-full left-0 z-50 mb-2 min-w-[220px] overflow-hidden rounded-xl border border-sage-600/40 bg-forest-900/95 shadow-2xl shadow-black/40 backdrop-blur-xl">
            <div className="p-1.5">
              <div className="px-2.5 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-sage-400">
                Answer style (MVP)
              </div>
              {answerModes.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => handleSelect(mode)}
                  className={`flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left transition-all duration-150 ${
                    selected.id === mode.id
                      ? 'bg-sage-600/30 text-cream-50'
                      : 'text-sage-200/90 hover:bg-cream-200/5 hover:text-cream-50'
                  }`}
                >
                  <div className="shrink-0">{mode.icon}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{mode.name}</span>
                      {mode.badge ? (
                        <span className="rounded-full bg-sage-500/25 px-1.5 py-0.5 text-[10px] font-medium text-cream-100">
                          {mode.badge}
                        </span>
                      ) : null}
                    </div>
                    <span className="text-[11px] text-sage-400">{mode.description}</span>
                  </div>
                  {selected.id === mode.id ? <Check className="size-4 shrink-0 text-sage-200" /> : null}
                </button>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}

function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled,
  submitting,
  placeholder,
  language,
  onLanguageChange,
}: {
  value: string
  onChange: (v: string) => void
  onSubmit: () => void
  disabled?: boolean
  submitting?: boolean
  placeholder?: string
  language: string
  onLanguageChange: (v: string) => void
}) {
  const [showAttachMenu, setShowAttachMenu] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [value])

  const handleSubmit = () => {
    if (!value.trim() || disabled || submitting) return
    onSubmit()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="relative mx-auto w-full max-w-[680px]">
      <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-b from-cream-200/15 to-transparent" />
      <div className="relative rounded-2xl bg-forest-800/90 shadow-[0_0_0_1px_rgba(243,238,237,0.08),0_2px_24px_rgba(0,0,0,0.35)] ring-1 ring-cream-200/10">
        <textarea
          ref={textareaRef}
          id="immigration-question"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={3}
          className="max-h-[200px] min-h-[88px] w-full resize-none bg-transparent px-5 pb-2 pt-5 text-[15px] text-cream-100 placeholder:text-sage-500/80 focus:outline-none"
        />

        <div className="flex items-center justify-between gap-2 px-3 pb-3 pt-1">
          <div className="flex items-center gap-1">
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowAttachMenu(!showAttachMenu)}
                className="flex size-8 items-center justify-center rounded-full bg-cream-200/10 text-sage-300 transition-all duration-200 hover:bg-cream-200/15 hover:text-cream-50 active:scale-95"
                aria-expanded={showAttachMenu}
                aria-haspopup="menu"
              >
                <Plus className={`size-4 transition-transform duration-200 ${showAttachMenu ? 'rotate-45' : ''}`} />
              </button>

              {showAttachMenu ? (
                <>
                  <button type="button" className="fixed inset-0 z-40 cursor-default bg-transparent" aria-label="Close menu" onClick={() => setShowAttachMenu(false)} />
                  <div
                    role="menu"
                    className="absolute bottom-full left-0 z-50 mb-2 min-w-[200px] overflow-hidden rounded-xl border border-sage-600/40 bg-forest-900/95 shadow-2xl shadow-black/40 backdrop-blur-xl"
                  >
                    <div className="p-1.5">
                      <p className="px-3 py-2 text-[11px] leading-snug text-sage-400">
                        File uploads are disabled in the MVP. Paste text only. Do not include emergency details.
                      </p>
                      <Link
                        href="/about"
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-sage-200/90 transition hover:bg-cream-200/5 hover:text-cream-50"
                        onClick={() => setShowAttachMenu(false)}
                      >
                        <Paperclip className="size-4 shrink-0" />
                        Legal &amp; privacy overview
                      </Link>
                    </div>
                  </div>
                </>
              ) : null}
            </div>
            <ModeSelector />
          </div>

          <select
            aria-label="Response language"
            value={language}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="max-w-[7.5rem] shrink-0 rounded-full border border-sage-600/40 bg-forest-900/80 px-2 py-1.5 text-[11px] font-medium text-cream-200 outline-none focus-visible:ring-2 focus-visible:ring-sage-400 sm:max-w-none sm:text-xs"
          >
            <option value="en">English</option>
            <option value="es" disabled>
              Spanish (soon)
            </option>
            <option value="zh" disabled>
              Chinese (soon)
            </option>
            <option value="fr" disabled>
              French (soon)
            </option>
          </select>

          <div className="hidden flex-1 sm:block" />

          <div className="flex items-center gap-2">
            <Link
              href="/scenarios"
              className="flex items-center gap-1.5 rounded-full px-2 py-2 text-xs font-medium text-sage-400 transition-all duration-200 hover:bg-cream-200/5 hover:text-cream-50 sm:px-3"
            >
              <Library className="size-4 shrink-0" />
              <span className="hidden sm:inline">Guides</span>
            </Link>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={!value.trim() || disabled || submitting}
              className="flex items-center gap-2 rounded-full bg-sage-500 px-3 py-2 text-sm font-medium text-cream-50 shadow-[0_0_18px_rgba(86,116,112,0.35)] transition-all duration-200 hover:bg-sage-600 disabled:cursor-not-allowed disabled:opacity-40 active:scale-95 sm:px-4"
            >
              <span className="hidden sm:inline">{submitting ? 'Working…' : 'Get information'}</span>
              {submitting ? (
                <span className="inline-block size-4 animate-spin rounded-full border-2 border-cream-200/30 border-t-cream-50 sm:hidden" />
              ) : (
                <SendHorizontal className="size-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function RayBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 select-none overflow-hidden">
      <div className="absolute inset-0 bg-[#0C2924]" />
      <div
        className="absolute left-1/2 top-[-10%] h-[70%] w-[180%] -translate-x-1/2 opacity-50 sm:w-[140%]"
        style={{
          background:
            'radial-gradient(ellipse 55% 50% at 50% 0%, rgba(86, 116, 112, 0.42) 0%, rgba(12, 41, 36, 0.25) 42%, transparent 72%)',
        }}
      />
      <div
        className="absolute left-1/2 top-1/3 h-[120%] w-[120%] -translate-x-1/2 opacity-30"
        style={{
          background:
            'radial-gradient(circle at 50% 40%, rgba(243, 238, 237, 0.12) 0%, transparent 55%)',
        }}
      />
    </div>
  )
}

function AnnouncementBadge({ text, href }: { text: string; href?: string }) {
  const className =
    'relative inline-flex min-h-[40px] items-center gap-2 overflow-hidden rounded-full px-5 py-2 text-sm font-medium text-cream-50 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]'
  const style: React.CSSProperties = {
    background: 'linear-gradient(135deg, rgba(86,116,112,0.35), rgba(12,41,36,0.5))',
    backdropFilter: 'blur(16px) saturate(130%)',
    boxShadow:
      'inset 0 1px rgba(243,238,237,0.15), inset 0 -1px rgba(0,0,0,0.12), 0 8px 28px -8px rgba(0,0,0,0.35), 0 0 0 1px rgba(243,238,237,0.1)',
  }

  const inner = (
    <>
      <span
        className="pointer-events-none absolute left-0 right-0 top-0 h-1/2 opacity-60 mix-blend-overlay"
        style={{
          background: 'radial-gradient(ellipse at center top, rgba(243, 238, 237, 0.18) 0%, transparent 70%)',
        }}
      />
      <Scale className="relative z-10 size-4 text-cream-100" aria-hidden />
      <span className="relative z-10">{text}</span>
    </>
  )

  if (href && href !== '#') {
    return (
      <a href={href} className={className} style={style} target="_blank" rel="noopener noreferrer">
        {inner}
      </a>
    )
  }
  return (
    <span className={className} style={style}>
      {inner}
    </span>
  )
}

function QuickLinks() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-6">
      <span className="text-sm text-sage-400">Also explore</span>
      <div className="flex flex-wrap justify-center gap-2">
        <Link
          href="/scenarios"
          className="flex items-center gap-1.5 rounded-full border border-cream-200/10 bg-forest-900/60 px-3 py-1.5 text-xs font-medium text-sage-200/90 transition-all duration-200 hover:border-sage-500/40 hover:bg-forest-800/80 hover:text-cream-50 active:scale-95"
        >
          <Library className="size-4" />
          Scenario guides
        </Link>
        <a
          href="https://www.uscis.gov/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 rounded-full border border-cream-200/10 bg-forest-900/60 px-3 py-1.5 text-xs font-medium text-sage-200/90 transition-all duration-200 hover:border-sage-500/40 hover:bg-forest-800/80 hover:text-cream-50 active:scale-95"
        >
          <MapPin className="size-4" />
          USCIS.gov
        </a>
        <a
          href="https://www.law.cornell.edu/uscode/text/8"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 rounded-full border border-cream-200/10 bg-forest-900/60 px-3 py-1.5 text-xs font-medium text-sage-200/90 transition-all duration-200 hover:border-sage-500/40 hover:bg-forest-800/80 hover:text-cream-50 active:scale-95"
        >
          <FileText className="size-4" />
          INA (Title 8)
        </a>
      </div>
    </div>
  )
}

export interface BoltStyleChatProps {
  title?: string
  titleAccent?: string
  titleSuffix?: string
  subtitle?: string
  announcementText?: string
  announcementHref?: string
  placeholder?: string
  message: string
  onMessageChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
  submitting?: boolean
  language: string
  onLanguageChange: (value: string) => void
}

export function BoltStyleChat({
  title = 'What do you need to know about',
  titleAccent = 'U.S. immigration',
  titleSuffix = 'today?',
  subtitle = 'Ask in plain language. Answers are designed to cite retrieved official materials—not unchecked model memory.',
  announcementText = 'Privacy-first legal information (MVP)',
  announcementHref,
  placeholder = 'Example: Can I travel while my green card application is pending?',
  message,
  onMessageChange,
  onSubmit,
  disabled,
  submitting,
  language,
  onLanguageChange,
}: BoltStyleChatProps) {
  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-sage-700/40 bg-[#0C2924] shadow-xl">
      <RayBackground />
      <form
        className="relative z-[1] flex flex-col items-center px-4 py-10 sm:px-8 sm:py-12"
        onSubmit={(e) => {
          e.preventDefault()
          if (!message.trim() || disabled || submitting) return
          onSubmit()
        }}
      >
        <div className="mb-6 flex justify-center">
          <AnnouncementBadge text={announcementText} href={announcementHref} />
        </div>

        <div className="mx-auto mb-6 max-w-3xl text-center">
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-cream-50 sm:text-4xl lg:text-5xl">
            {title}{' '}
            <span className="bg-gradient-to-b from-sage-300 via-sage-200 to-cream-100 bg-clip-text italic text-transparent">
              {titleAccent}
            </span>{' '}
            {titleSuffix}
          </h1>
          <p className="text-sm font-medium text-sage-300/95 sm:text-base">{subtitle}</p>
        </div>

        <div className="mb-8 w-full">
          <ChatInput
            value={message}
            onChange={onMessageChange}
            onSubmit={onSubmit}
            disabled={disabled}
            submitting={submitting}
            placeholder={placeholder}
            language={language}
            onLanguageChange={onLanguageChange}
          />
        </div>

        <QuickLinks />
      </form>
    </div>
  )
}
