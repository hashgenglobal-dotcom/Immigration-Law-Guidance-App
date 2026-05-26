import Image from 'next/image'

export function SourcePathLogo({ size = 36 }: { size?: number }) {
  return (
    <Image
      src="/sourcepath-icon.png"
      alt=""
      width={size}
      height={size}
      className="shrink-0 rounded-lg"
      priority
    />
  )
}
