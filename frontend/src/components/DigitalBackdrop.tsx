/** Parchment wash + subtle dot grid — mirrors mobile DigitalBackdrop */
export function DigitalBackdrop({ variant = 'home' }: { variant?: 'home' | 'ask' | 'scenarios' | 'about' }) {
  const bronzeOpacity = variant === 'ask' ? 0.09 : 0.07
  const navyOpacity = variant === 'scenarios' || variant === 'about' ? 0.08 : 0.06

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-parchment" aria-hidden>
      <div
        className="absolute inset-x-0 top-0 h-[45%]"
        style={{ backgroundColor: `rgba(156, 123, 92, ${bronzeOpacity})` }}
      />
      <div
        className="absolute inset-x-0 bottom-0 h-[40%]"
        style={{ backgroundColor: `rgba(31, 40, 57, ${navyOpacity})` }}
      />
      <div
        className="absolute inset-0 opacity-[0.14]"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(31,40,57,0.35) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      />
    </div>
  )
}
