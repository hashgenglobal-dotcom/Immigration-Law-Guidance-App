export default function Footer() {
  return (
    <footer className="bg-gray-800 text-gray-300 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-white font-semibold mb-2">Legal Disclaimer</h3>
            <p className="text-sm">
              This application provides general legal information only. It is not legal advice
              and does not create an attorney-client relationship. Immigration law is complex and
              fact-specific. Always consult with a qualified immigration attorney for your
              specific situation.
            </p>
          </div>
          <div>
            <h3 className="text-white font-semibold mb-2">Emergency Notice</h3>
            <p className="text-sm">
              If you are facing an immigration emergency or are in removal proceedings, contact
              an immigration attorney immediately. Do not rely solely on this application for
              urgent legal matters.
            </p>
          </div>
        </div>
        <div className="border-t border-gray-700 mt-6 pt-6 text-sm text-center">
          <p>&copy; {new Date().getFullYear()} HashGen Global LLC. Privacy-first legal information assistant.</p>
        </div>
      </div>
    </footer>
  )
}
