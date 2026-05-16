'use client'

import { useCallback, useState } from 'react'
import Callout from '@/components/Callout'
import { ScrollReveal } from '@/components/ScrollReveal'
import PageHeader from '@/components/PageHeader'
import SourcesCitations from '@/components/SourcesCitations'
import { BoltStyleChat } from '@/components/ui/bolt-style-chat'

type AnswerPayload = {
  shortAnswer: string
  simpleExplanation: string
  possibleRisks: string[]
  whatToDoNext: string[]
  sources: Array<{
    title: string
    citation: string
    url: string
    type: 'regulation' | 'statute' | 'case' | 'guidance'
  }>
  disclaimer: string
}

export default function AskQuestionPage() {
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('en')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [answer, setAnswer] = useState<AnswerPayload | null>(null)

  const runSubmit = useCallback(async () => {
    if (!question.trim() || isSubmitting) return
    setIsSubmitting(true)
    setAnswer(null)

    try {
      const res = await fetch('/api/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, language }),
      })

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`)
      }

      const data = await res.json()
      const answerData = data.answer

      setAnswer({
        shortAnswer: answerData?.short_answer || 'No answer returned',
        simpleExplanation: answerData?.simple_explanation || '',
        possibleRisks: answerData?.possible_risks || [],
        whatToDoNext: answerData?.what_to_do_next || [],
        sources: (answerData?.official_sources || []).map((src: { title?: string; citation: string; official_url: string }) => ({
          title: src.title || src.citation,
          citation: src.citation,
          url: src.official_url,
          type: 'regulation' as const,
        })),
        disclaimer:
          answerData?.legal_disclaimer ||
          'This is general legal information, not legal advice. Consult with an immigration attorney for your specific situation.',
      })
    } catch (err) {
      setAnswer({
        shortAnswer: 'Error connecting to backend',
        simpleExplanation: `Failed to get answer: ${err instanceof Error ? err.message : 'Unknown error'}. Ensure the backend is running on port 8000.`,
        possibleRisks: [],
        whatToDoNext: ['Check that the backend server is running', 'Verify the API endpoint is accessible'],
        sources: [],
        disclaimer: 'This is general legal information, not legal advice.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }, [question, language, isSubmitting])

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 sm:py-12 lg:px-8">
      <PageHeader
        eyebrow="Assistant"
        title="Ask a question"
        description="Use the composer below. The shipped product will retrieve official sources before answering."
      />

      <Callout variant="warning" title="Privacy note">
        <p>
          Do not enter emergency information. Full questions are not stored by default. This system is designed to
          minimize data retention.
        </p>
      </Callout>

      <ScrollReveal className="mt-8">
        <BoltStyleChat
          message={question}
          onMessageChange={setQuestion}
          onSubmit={runSubmit}
          disabled={false}
          submitting={isSubmitting}
          language={language}
          onLanguageChange={setLanguage}
        />
      </ScrollReveal>

      {answer ? (
        <ScrollReveal className="mt-12">
          <AnswerDisplay answer={answer} />
        </ScrollReveal>
      ) : isSubmitting ? (
        <ScrollReveal className="mt-12">
          <LoadingAnswerSkeleton />
        </ScrollReveal>
      ) : null}
    </div>
  )
}

function LoadingAnswerSkeleton() {
  return (
    <div className="space-y-6">
      {/* Short Answer skeleton */}
      <div className="animate-pulse rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
        <div className="h-4 w-24 rounded bg-sage-200" />
        <div className="mt-4 h-6 w-48 rounded bg-sage-200" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-sage-200" />
          <div className="h-4 w-5/6 rounded bg-sage-200" />
        </div>
      </div>

      {/* Simple Explanation skeleton */}
      <div className="animate-pulse rounded-2xl border border-sage-200 bg-cream-100 p-6 sm:p-8">
        <div className="h-5 w-40 rounded bg-sage-200" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-sage-200" />
          <div className="h-4 w-11/12 rounded bg-sage-200" />
          <div className="h-4 w-4/5 rounded bg-sage-200" />
        </div>
      </div>

      {/* Possible Risks skeleton */}
      <div className="animate-pulse rounded-2xl border border-sage-300 bg-sage-50 p-6 sm:p-8">
        <div className="h-5 w-32 rounded bg-sage-200" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-sage-200" />
          <div className="h-4 w-3/4 rounded bg-sage-200" />
        </div>
      </div>

      {/* What To Do Next skeleton */}
      <div className="animate-pulse rounded-2xl border border-sage-200 bg-cream-50 p-6 sm:p-8">
        <div className="h-5 w-36 rounded bg-sage-200" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-sage-200" />
          <div className="h-4 w-5/6 rounded bg-sage-200" />
        </div>
      </div>

      {/* Sources skeleton */}
      <div className="animate-pulse rounded-2xl border border-sage-200 bg-cream-50 p-6 sm:p-8">
        <div className="h-5 w-28 rounded bg-sage-200" />
        <div className="mt-4 space-y-3">
          <div className="h-12 w-full rounded bg-sage-200" />
          <div className="h-12 w-3/4 rounded bg-sage-200" />
        </div>
      </div>
    </div>
  )
}

function AnswerDisplay({ answer }: { answer: AnswerPayload }) {
  return (
    <div className="space-y-6">
      {/* Short Answer with fade-in animation */}
      <div className="animate-fade-in-up rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">Summary</p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-forest-900">Short answer</h2>
        <p className="mt-4 text-lg leading-relaxed text-sage-900">{answer.shortAnswer}</p>
      </div>

      {/* Simple Explanation with staggered animation */}
      <div className="animate-fade-in-up-delay-1 rounded-2xl border border-sage-200 bg-cream-100 p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-forest-900">Simple explanation</h2>
        <p className="mt-3 leading-relaxed text-sage-900">{answer.simpleExplanation}</p>
      </div>

      {/* Possible Risks with slide animation */}
      <div className="animate-fade-in-up-delay-2 rounded-2xl border border-sage-300 bg-sage-50 p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-forest-900">Possible risks</h2>
        <ul className="mt-4 space-y-2">
          {answer.possibleRisks.map((risk, i) => (
            <li key={i} className="flex gap-2 text-sm leading-relaxed text-forest-900/90">
              <span className="mt-0.5 font-semibold">•</span>
              <span>{risk}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* What To Do Next with staggered animation */}
      <div className="animate-fade-in-up-delay-3 rounded-2xl border border-sage-200 bg-cream-50 p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-forest-900">What to do next</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-sage-900">
          {answer.whatToDoNext.map((step, i) => (
            <li key={i} className="pl-1">
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Sources with slide animation */}
      <div className="animate-fade-in-up-delay-4">
        <SourcesCitations sources={answer.sources} />
      </div>

      {/* Disclaimer with final animation */}
      <div className="animate-fade-in-up-delay-5">
        <Callout variant="warning" title="Legal disclaimer">
          <p>{answer.disclaimer}</p>
        </Callout>
      </div>
    </div>
  )
}
