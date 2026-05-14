import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-900 to-primary-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Immigration Law Guidance App
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-primary-100">
            Privacy-first immigration law information assistant
          </p>
          <div className="bg-yellow-100 text-yellow-900 px-6 py-3 rounded-lg inline-block mb-8">
            <p className="text-sm font-medium">
              ⚖️ This is general legal information, not legal advice.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/ask"
              className="bg-white text-primary-700 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors shadow-lg"
            >
              Ask a Question
            </Link>
            <Link
              href="/scenarios"
              className="bg-primary-800 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-primary-900 transition-colors shadow-lg border border-primary-600"
            >
              Browse Common Scenarios
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">❓</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Ask Questions</h3>
              <p className="text-gray-600">
                Get clear, plain-language explanations about immigration law and your rights.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🔒</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Privacy-First</h3>
              <p className="text-gray-600">
                Your questions are processed locally. No data is sent to external AI services.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📚</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Official Sources</h3>
              <p className="text-gray-600">
                All information is backed by CFR, USCIS, and other official government sources.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Common Scenarios Preview */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-4">
            Common Scenarios
          </h2>
          <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            Quick guides for frequently asked immigration situations
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <ScenarioCard
              title="ICE came to my door"
              riskLevel="high"
              description="Know your rights when immigration officers arrive"
            />
            <ScenarioCard
              title="I overstayed my visa"
              riskLevel="medium"
              description="Understanding your options after visa expiration"
            />
            <ScenarioCard
              title="I received a Notice to Appear"
              riskLevel="high"
              description="What to do when placed in removal proceedings"
            />
            <ScenarioCard
              title="I want to apply for asylum"
              riskLevel="medium"
              description="Asylum application process and requirements"
            />
            <ScenarioCard
              title="I want to apply for citizenship"
              riskLevel="low"
              description="Naturalization process for permanent residents"
            />
            <ScenarioCard
              title="I lost an immigration document"
              riskLevel="medium"
              description="How to replace lost immigration documents"
            />
          </div>
          <div className="text-center mt-8">
            <Link
              href="/scenarios"
              className="text-primary-600 hover:text-primary-800 font-medium"
            >
              View All Scenarios →
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

function ScenarioCard({
  title,
  riskLevel,
  description,
}: {
  title: string
  riskLevel: 'low' | 'medium' | 'high'
  description: string
}) {
  const riskColors = {
    low: 'bg-green-100 text-green-800 border-green-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    high: 'bg-red-100 text-red-800 border-red-300',
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <span
          className={`text-xs px-2 py-1 rounded-full border ${riskColors[riskLevel]}`}
        >
          {riskLevel.toUpperCase()}
        </span>
      </div>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}
