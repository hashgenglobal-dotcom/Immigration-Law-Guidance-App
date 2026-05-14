export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">About This App</h1>

      <div className="prose prose-lg max-w-none">
        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Mission</h2>
          <p className="text-gray-700">
            This application provides privacy-first immigration law information to help individuals
            understand their rights and navigate the U.S. immigration system. All processing happens
            locally - no data is sent to external AI services or cloud providers.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">What This App Does</h2>
          <ul className="list-disc pl-6 space-y-2 text-gray-700">
            <li>Provides general legal information about immigration law</li>
            <li>Explains rights and procedures in plain language</li>
            <li>Links to official government sources (CFR, USCIS, INA)</li>
            <li>Offers scenario-based guides for common situations</li>
            <li>Processes all queries locally for privacy</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">What This App Does NOT Do</h2>
          <ul className="list-disc pl-6 space-y-2 text-gray-700">
            <li>Provide legal advice or legal representation</li>
            <li>Create an attorney-client relationship</li>
            <li>Replace consultation with a qualified immigration attorney</li>
            <li>Store your personal information or questions long-term</li>
            <li>Handle emergency situations or urgent legal matters</li>
          </ul>
        </section>

        <section className="mb-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-2xl font-semibold text-yellow-900 mb-4">⚖️ Legal Disclaimer</h2>
          <p className="text-yellow-800">
            <strong>This application provides general legal information only, not legal advice.</strong>{' '}
            Immigration law is complex and fact-specific. The information in this app may not apply
            to your specific situation. Always consult with a qualified immigration attorney for
            legal advice about your case.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Privacy & Data Security</h2>
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <p className="text-green-800">
              <strong>Privacy-First Design:</strong> This app is built to minimize data collection.
              Questions are processed locally and are not stored by default. No data is sent to
              external AI APIs (OpenAI, Anthropic, etc.). All AI processing happens on your device
              using local models.
            </p>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Technology Stack</h2>
          <ul className="list-disc pl-6 space-y-2 text-gray-700">
            <li><strong>Frontend:</strong> Next.js 15, React 19, TypeScript, Tailwind CSS</li>
            <li><strong>Backend:</strong> FastAPI (Python), PostgreSQL with pgvector</li>
            <li><strong>AI/ML:</strong> Ollama (local LLM), nomic-embed-text (embeddings)</li>
            <li><strong>Data Sources:</strong> eCFR (Cornell LII), USCIS, INA, BIA decisions</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Contact</h2>
          <p className="text-gray-700">
            Built by <strong>HashGen Global LLC</strong> - IT Services, Tech Staffing & AI Automation
          </p>
        </section>
      </div>
    </div>
  )
}
