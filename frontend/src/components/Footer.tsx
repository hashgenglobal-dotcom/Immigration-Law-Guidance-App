import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-sage-600/30 bg-forest-900 text-cream-200/90">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-3">
          <div className="md:col-span-2">
            <p className="text-sm font-semibold uppercase tracking-widest text-sage-400">Legal notice</p>
            <h3 className="mt-2 text-lg font-semibold text-cream-50">Disclaimer</h3>
            <p className="mt-3 text-sm leading-relaxed text-cream-200/85">
              This application provides general legal information only. It is not legal advice and does not create an
              attorney-client relationship. Immigration law is complex and fact-specific. Always consult with a qualified
              immigration attorney for your specific situation.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-cream-50">Emergency</h3>
            <p className="mt-3 text-sm leading-relaxed text-cream-200/85">
              If you are facing an immigration emergency or are in removal proceedings, contact an immigration attorney
              immediately. Do not rely solely on this application for urgent legal matters.
            </p>
            <div className="mt-6 flex flex-wrap gap-x-4 gap-y-2 text-sm">
              <Link className="font-medium text-sage-300 transition-colors duration-300 hover:text-cream-50" href="/ask">
                Ask a question
              </Link>
              <span className="text-sage-700" aria-hidden>
                ·
              </span>
              <Link className="font-medium text-sage-300 hover:text-cream-50" href="/scenarios">
                Scenario guides
              </Link>
              <span className="text-sage-700" aria-hidden>
                ·
              </span>
              <Link className="font-medium text-sage-300 hover:text-cream-50" href="/about">
                About
              </Link>
            </div>
          </div>
        </div>
        <div className="mt-10 border-t border-forest-800 pt-6 text-center text-xs text-sage-400">
          <p>
            &copy; {new Date().getFullYear()} HashGen Global LLC. Privacy-first legal information assistant.
          </p>
        </div>
      </div>
    </footer>
  )
}
