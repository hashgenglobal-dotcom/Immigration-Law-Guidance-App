import AboutUsSection from '@/components/ui/about-us-section'
import Callout from '@/components/Callout'

export default function AboutPage() {
  return (
    <>
      <AboutUsSection />

      <div className="mx-auto max-w-4xl space-y-10 px-4 py-12 sm:px-6 lg:px-8">
        <section className="surface-card p-6 sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">What this app does not do</h2>
          <ul className="mt-4 list-disc space-y-2 pl-6 leading-relaxed text-sage-900">
            <li>Provide legal advice or legal representation</li>
            <li>Create an attorney-client relationship</li>
            <li>Replace consultation with a qualified immigration attorney</li>
            <li>Store your personal information or questions long-term (by default)</li>
            <li>Handle emergency situations or urgent legal matters</li>
          </ul>
        </section>

        <Callout variant="warning" title="Legal disclaimer">
          <p>
            <strong>This application provides general legal information only, not legal advice.</strong> Immigration law
            is complex and fact-specific. The information in this app may not apply to your specific situation. Always
            consult with a qualified immigration attorney for legal advice about your case.
          </p>
        </Callout>

        <section className="surface-card p-6 sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">Technology stack</h2>
          <ul className="mt-4 list-disc space-y-2 pl-6 leading-relaxed text-sage-900">
            <li>
              <strong>Frontend:</strong> Next.js 15, React 19, TypeScript, Tailwind CSS
            </li>
            <li>
              <strong>Backend:</strong> FastAPI (Python), PostgreSQL with pgvector
            </li>
            <li>
              <strong>AI/ML:</strong> Ollama (local LLM), nomic-embed-text (embeddings)
            </li>
            <li>
              <strong>Data sources:</strong> eCFR (Cornell LII), USCIS, INA, BIA decisions
            </li>
          </ul>
        </section>

        <section className="surface-card p-6 sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">Contact</h2>
          <p className="mt-3 leading-relaxed text-sage-900">
            Built by <strong className="text-forest-900">HashGen Global LLC</strong> — IT services, tech staffing, and AI
            automation.
          </p>
        </section>
      </div>
    </>
  )
}
