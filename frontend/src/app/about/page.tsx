import Callout from '@/components/Callout'
import PageHeader from '@/components/PageHeader'

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Transparency"
        title="About this app"
        description="What we are building, what we are not building, and how privacy fits into the design."
      />

      <div className="space-y-10">
        <section className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">Mission</h2>
          <p className="mt-3 leading-relaxed text-sage-900">
            This application provides privacy-first immigration law information to help individuals understand their rights
            and navigate the U.S. immigration system. The goal is for processing to happen locally—without sending your
            personal facts to external AI services or cloud providers.
          </p>
        </section>

        <section className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">What this app does</h2>
          <ul className="mt-4 list-disc space-y-2 pl-6 leading-relaxed text-sage-900">
            <li>Provides general legal information about immigration law</li>
            <li>Explains rights and procedures in plain language</li>
            <li>Links to official government sources (CFR, USCIS, INA)</li>
            <li>Offers scenario-based guides for common situations</li>
            <li>Processes queries with a local-first posture</li>
          </ul>
        </section>

        <section className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
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
            <strong>This application provides general legal information only, not legal advice.</strong> Immigration law is
            complex and fact-specific. The information in this app may not apply to your specific situation. Always consult
            with a qualified immigration attorney for legal advice about your case.
          </p>
        </Callout>

        <section className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">Privacy and data security</h2>
          <div className="mt-4">
            <Callout variant="success" title="Privacy-first design">
              <p>
                This app is built to minimize data collection. Questions are processed with a local-first approach and are
                not stored by default. The target architecture avoids sending user prompts to external AI APIs (OpenAI,
                Anthropic, etc.) and relies on on-device or controlled infrastructure.
              </p>
            </Callout>
          </div>
        </section>

        <section className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
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

        <section className="rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm sm:p-8">
          <h2 className="text-xl font-semibold tracking-tight text-forest-900">Contact</h2>
          <p className="mt-3 leading-relaxed text-sage-900">
            Built by <strong className="text-forest-900">HashGen Global LLC</strong> — IT services, tech staffing, and AI automation.
          </p>
        </section>
      </div>
    </div>
  )
}
