'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function AskQuestionPage() {
  const router = useRouter()
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('en')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [answer, setAnswer] = useState<null | any>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    // TODO: Backend API integration will go here
    // Example: POST /api/answer with { question, language }
    // For now, using mock data
    
    setTimeout(() => {
      // Mock response - will be replaced with actual API call
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
            type: 'regulation' as const,
          },
        ],
        disclaimer: 'This is general legal information, not legal advice. Consult with an immigration attorney for your specific situation.',
      })
      setIsSubmitting(false)
    }, 1000)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Ask a Question</h1>
      
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-8">
        <p className="text-sm text-yellow-800">
          <strong>Privacy Note:</strong> Do not enter emergency information. Full questions are not stored by default.
          This system is designed to minimize data retention.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
            Your Immigration Question
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={6}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            placeholder="Describe your situation or ask a specific question..."
            required
          />
        </div>

        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
            Language (Coming Soon)
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="en">English</option>
            <option value="es" disabled>Spanish (Coming Soon)</option>
            <option value="zh" disabled>Chinese (Coming Soon)</option>
            <option value="fr" disabled>French (Coming Soon)</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !question.trim()}
          className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Processing...' : 'Get Information'}
        </button>
      </form>

      {answer && (
        <div className="mt-12">
          <AnswerDisplay answer={answer} />
        </div>
      )}
    </div>
  )
}

function AnswerDisplay({ answer }: { answer: any }) {
  return (
    <div className="space-y-8">
      <div className="border-t-4 border-primary-600 pt-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Short Answer</h2>
        <p className="text-lg text-gray-700">{answer.shortAnswer}</p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-3">Simple Explanation</h2>
        <p className="text-gray-700">{answer.simpleExplanation}</p>
      </div>

      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-red-900 mb-3">⚠️ Possible Risks</h2>
        <ul className="space-y-2">
          {answer.possibleRisks.map((risk: string, i: number) => (
            <li key={i} className="text-red-800 flex items-start">
              <span className="mr-2">•</span>
              {risk}
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-green-900 mb-3">✅ What To Do Next</h2>
        <ol className="space-y-2 list-decimal list-inside">
          {answer.whatToDoNext.map((step: string, i: number) => (
            <li key={i} className="text-green-800">{step}</li>
          ))}
        </ol>
      </div>

      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Official Sources</h2>
        <ul className="space-y-3">
          {answer.sources.map((source: any, i: number) => (
            <li key={i} className="border-l-4 border-primary-600 pl-4">
              <p className="text-sm font-medium text-gray-900">{source.title}</p>
              <p className="text-xs text-gray-500">{source.citation}</p>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-800 text-sm"
              >
                View Source →
              </a>
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>⚖️ Legal Disclaimer:</strong> {answer.disclaimer}
        </p>
      </div>
    </div>
  )
}
