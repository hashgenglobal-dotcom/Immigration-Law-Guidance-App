import { useMemo } from 'react'
import { StyleSheet, View } from 'react-native'
import { colors } from '@/theme'

/** Lightweight procedural dot pattern */
export function DotGrid({ columns = 14, rows = 24, opacity = 0.12 }: {
  columns?: number
  rows?: number
  opacity?: number
}) {
  const dots = useMemo(() => {
    const items: { key: string; left: `${number}%`; top: number }[] = []
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < columns; c += 1) {
        items.push({
          key: `${r}-${c}`,
          left: `${(c / (columns - 1)) * 100}%` as `${number}%`,
          top: r * 28,
        })
      }
    }
    return items
  }, [columns, rows])

  return (
    <View style={[styles.wrap, { opacity }]} pointerEvents="none">
      {dots.map((d) => (
        <View key={d.key} style={[styles.dot, { left: d.left, top: d.top }]} />
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    ...StyleSheet.absoluteFillObject,
  },
  dot: {
    position: 'absolute',
    width: 2,
    height: 2,
    borderRadius: 1,
    backgroundColor: colors.brandNavy,
    marginLeft: -1,
  },
})
