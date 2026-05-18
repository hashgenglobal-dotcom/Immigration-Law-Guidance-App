import type { ReactNode } from 'react'
import { Image, StyleSheet, View } from 'react-native'
import { appImages } from '@/assets/images'
import { ImageFadeOverlay } from '@/components/ui/ImageFadeOverlay'
import { cardStandard, colors, spacing } from '@/theme'

/** Elevated principles block with digital hero strip header */
export function AboutPrinciplesPanel({ children }: { children: ReactNode }) {
  return (
    <View style={styles.panel}>
      <View style={styles.digitalStrip}>
        <Image source={appImages.heroAccent} style={styles.stripImage} resizeMode="cover" />
        <ImageFadeOverlay variant="light" />
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
  inner: {
    padding: spacing.md,
    paddingTop: spacing.sm,
    backgroundColor: colors.surfaceWhite,
  },
})
