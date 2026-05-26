'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { LEGAL_DISCLAIMER_SHORT, LEGAL_DISCLAIMER_FULL } from '@/lib/legalCopy'

export function LegalDisclaimerAccordion() {
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-10 rounded-2xl border border-bronze-200/80 bg-parchment-50">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-semibold text-navy-800 sm:px-5"
        aria-expanded={open}
      >
        <span>Legal disclaimer</span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-bronze-600 transition ${open ? 'rotate-180' : ''}`} aria-hidden />
      </button>
      {open ? (
        <div className="border-t border-bronze-100 px-4 pb-4 pt-2 text-sm leading-relaxed text-bronze-800 sm:px-5">
          <p>{LEGAL_DISCLAIMER_SHORT}</p>
          <p className="mt-3">{LEGAL_DISCLAIMER_FULL}</p>
        </div>
      ) : (
        <p className="border-t border-bronze-100 px-4 pb-4 pt-0 text-sm leading-relaxed text-bronze-800 sm:px-5">
          {LEGAL_DISCLAIMER_SHORT}
        </p>
      )}
    </div>
  )
}
