export default function PageHeader({
  title,
  description,
  eyebrow,
}: {
  title: string
  description?: string
  eyebrow?: string
}) {
  return (
    <header className="mb-10 border-b border-sage-200/80 pb-8">
      {eyebrow ? (
        <p className="text-xs font-semibold uppercase tracking-widest text-sage-600">{eyebrow}</p>
      ) : null}
      <div className="mt-2 h-1 w-14 rounded-full bg-gradient-to-r from-sage-500 to-sage-300" aria-hidden />
      <h1 className="mt-3 text-3xl font-bold tracking-tight text-forest-900 sm:text-4xl">{title}</h1>
      {description ? (
        <p className="mt-3 max-w-2xl text-lg text-sage-800 leading-relaxed">{description}</p>
      ) : null}
    </header>
  )
}
