'use client'

import { useState } from 'react'
import Link from 'next/link'

interface Scenario {
  id: string
  title: string
  riskLevel: 'low' | 'medium' | 'high'
  description: string
  shortDescription: string
}

const scenarios: Scenario[] = [
  {
    id: 'ice-door',
    title: 'ICE came to my door',
    riskLevel: 'high',
    description: 'Immigration officers are at your residence',
    shortDescription: 'Know your rights when ICE agents arrive',
  },
  {
    id: 'overstay',
    title: 'I overstayed my visa',
    riskLevel: 'medium',
    description: 'Your visa has expired and you are out of status',
    shortDescription: 'Understanding options after visa expiration',
  },
  {
    id: 'nta',
    title: 'I received a Notice to Appear',
    riskLevel: 'high',
    description: 'You have been placed in removal proceedings',
    shortDescription: 'What to do after receiving an NTA',
  },
  {
    id: 'asylum',
    title: 'I want to apply for asylum',
    riskLevel: 'medium',
    description: 'Seeking protection due to persecution in home country',
    shortDescription: 'Asylum application process and requirements',
  },
  {
    id: 'citizenship',
    title: 'I want to apply for citizenship',
    riskLevel: 'low',
    description: 'Naturalization process for permanent residents',
    shortDescription: 'N-400 application requirements',
  },
  {
    id: 'lost-document',
    title: 'I lost an immigration document',
    riskLevel: 'medium',
    description: 'Replacement procedures for lost documents',
    shortDescription: 'How to replace lost immigration documents',
  },
]

export default function ScenariosPage() {
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Scenario Guides</h1>
      
      <p className="text-lg text-gray-600 mb-8">
        Select a scenario below to learn about your rights and next steps. 
        These are general guides - consult an attorney for your specific situation.
      </p>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {scenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            onClick={() => setSelectedScenario(scenario)}
          />
        ))}
      </div>

      {selectedScenario && (
        <ScenarioModal
          scenario={selectedScenario}
          onClose={() => setSelectedScenario(null)}
        />
      )}
    </div>
  )
}

function ScenarioCard({
  scenario,
  onClick,
}: {
  scenario: Scenario
  onClick: () => void
}) {
  const riskColors = {
    low: 'bg-green-100 text-green-800 border-green-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    high: 'bg-red-100 text-red-800 border-red-300',
  }

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">{scenario.title}</h3>
        <span
          className={`text-xs px-2 py-1 rounded-full border ${riskColors[scenario.riskLevel]}`}
        >
          {scenario.riskLevel.toUpperCase()}
        </span>
      </div>
      <p className="text-gray-600 text-sm">{scenario.shortDescription}</p>
      <p className="text-primary-600 text-sm mt-4 font-medium">Click to learn more →</p>
    </div>
  )
}

function ScenarioModal({
  scenario,
  onClose,
}: {
  scenario: Scenario
  onClose: () => void
}) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">{scenario.title}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>
          
          <div className="mb-6">
            <span
              className={`inline-block text-xs px-3 py-1 rounded-full border ${
                scenario.riskLevel === 'high'
                  ? 'bg-red-100 text-red-800 border-red-300'
                  : scenario.riskLevel === 'medium'
                  ? 'bg-yellow-100 text-yellow-800 border-yellow-300'
                  : 'bg-green-100 text-green-800 border-green-300'
              }`}
            >
              {scenario.riskLevel.toUpperCase()} RISK
            </span>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Situation</h3>
              <p className="text-gray-700">{scenario.description}</p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">⚠️ Important</h3>
              <p className="text-blue-800 text-sm">
                This is a placeholder guide. Backend integration pending. 
                In the final version, this will contain detailed legal information,
                rights, procedures, and official sources.
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">⚖️ Legal Disclaimer</h3>
              <p className="text-yellow-800 text-sm">
                This is general legal information, not legal advice. Consult with an
                immigration attorney for your specific situation.
              </p>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="bg-primary-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-primary-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
