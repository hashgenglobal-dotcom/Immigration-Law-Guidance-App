import type { ReactNode } from 'react'
import { Image, StyleSheet, View } from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { appImages } from '@/assets/images'
import { cardStandard, colors, radii, spacing } from '@/theme'

/** Elevated principles block with digital hero strip header */
export function AboutPrinciplesPanel({ children }: { children: ReactNode }) {
  return (
    <View style={styles.panel}>
      <View style={styles.digitalStrip}>
        <Image source={appImages.heroAccent} style={styles.stripImage} resizeMode="cover" />
        <LinearGradient
          colors={['rgba(255,255,255,0.15)', 'rgba(244,241,234,0.92)', colors.parchment]}
          locations={[0, 0.45, 1]}
          style={styles.stripFade}
        />
      </View>
      <View style={styles.inner}>{children}</View>
    </View>
  )
}

const styles = StyleSheet.create({
  panel: {
    marginBottom: spacing.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
    ...cardStandard,
  },
  digitalStrip: {
    height: 72,
    width: '100%',
    overflow: 'hidden',
  },
  stripImage: {
    width: '100%',
    height: '100%',
    opacity: 0.85,
  },
  stripFade: {
    ...StyleSheet.absoluteFillObject,
  },
  inner: {
    padding: spacing.md,
    paddingTop: spacing.sm,
    backgroundColor: colors.surfaceWhite,
  },
})
