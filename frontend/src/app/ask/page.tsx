'use client'

import { useCallback, useState } from 'react'
import Callout from '@/components/Callout'
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

  const runSubmit = useCallback(() => {
    if (!question.trim() || isSubmitting) return
    setIsSubmitting(true)

    // TODO: Backend API integration will go here
    setTimeout(() => {
      setAnswer({
        shortAnswer: 'This is a placeholder answer. Backend integration pending.',
        simpleExplanation: 'This section will contain a clear, plain-language explanation of the legal issue.',
        possibleRisks: [
          'Risk 1: Placeholder - backend will provide actual risks',
          'Risk 2: Placeholder - backend will provide actual risks',
        ],
        whatToDoNext: [
          'Step 1: Placeholder - backend will provide actionable steps',
          'Step 2: Placeholder - backend will provide actionable steps',
        ],
        sources: [
          {
            title: '8 CFR § 208.7 - Employment authorization',
            citation: '8 CFR 208.7',
            url: 'https://www.law.cornell.edu/cfr/text/8/208.7',
            type: 'regulation',
          },
        ],
        disclaimer:
          'This is general legal information, not legal advice. Consult with an immigration attorney for your specific situation.',
      })
      setIsSubmitting(false)
    }, 900)
  }, [question, isSubmitting])

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

      <div className="mt-8">
        <BoltStyleChat
          message={question}
          onMessageChange={setQuestion}
          onSubmit={runSubmit}
          disabled={false}
          submitting={isSubmitting}
          language={language}
          onLanguageChange={setLanguage}
        />
      </div>

      {answer ? (
        <div className="mt-12">
          <AnswerDisplay answer={answer} />
        </div>
      ) : null}
    </div>
  )
}

function AnswerDisplay({ answer }: { answer: AnswerPayload }) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
        <p className="text-xs font-semibold uppercase tracking-wide text-sage-700">Summary</p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-forest-900">Short answer</h2>
        <p className="mt-4 text-lg leading-relaxed text-sage-900">{answer.shortAnswer}</p>
      </div>

      <div className="rounded-2xl border border-sage-200 bg-cream-100 p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-forest-900">Simple explanation</h2>
        <p className="mt-3 leading-relaxed text-sage-900">{answer.simpleExplanation}</p>
      </div>

      <div className="rounded-2xl border border-sage-300 bg-sage-50 p-6 sm:p-8">
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

      <div className="rounded-2xl border border-sage-200 bg-cream-50 p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-forest-900">What to do next</h2>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-sage-900">
          {answer.whatToDoNext.map((step, i) => (
            <li key={i} className="pl-1">
              {step}
            </li>
          ))}
        </ol>
      </div>

      <SourcesCitations sources={answer.sources} />

      <Callout variant="warning" title="Legal disclaimer">
        <p>{answer.disclaimer}</p>
      </Callout>
    </div>
  )
}
