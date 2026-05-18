import { Image, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { appImages } from '@/assets/images'
import { ImageFadeOverlay } from '@/components/ui/ImageFadeOverlay'
import { NavyBackground } from '@/components/ui/NavyBackground'
import { brand } from '@/lib/brand'
import { colors, fontFamily, radii, shadows, spacing } from '@/theme'

export function AboutFooter() {
  return (
    <View style={styles.wrap}>
      <View style={styles.gradient}>
        <NavyBackground />
        <View style={styles.watermarkWrap} pointerEvents="none">
          <Image source={appImages.heroAccent} style={styles.watermark} resizeMode="cover" />
        </View>
        <ImageFadeOverlay variant="dark" />
        <View style={styles.content}>
          <View style={styles.topRule} />
          <View style={styles.brandRow}>
            <View style={styles.shieldSeal}>
              <Ionicons name="shield-checkmark" size={22} color={colors.surfaceWhite} />
            </View>
            <View style={styles.brandCopy}>
              <Text style={styles.brandName}>{brand.name}</Text>
              <Text style={styles.brandTagline}>{brand.tagline}</Text>
            </View>
          </View>
          <View style={styles.metaRow}>
            <Text style={styles.meta}>{brand.motto}</Text>
            <View style={styles.metaDot} />
            <Text style={styles.meta}>{brand.company}</Text>
          </View>
          <Text style={styles.previewNote}>Mobile preview · Mock data only</Text>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    borderRadius: radii.card,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
    ...shadows.soft,
  },
  gradient: {
    position: 'relative',
    overflow: 'hidden',
    backgroundColor: colors.brandNavy,
  },
  watermarkWrap: {
    position: 'absolute',
    right: -40,
    bottom: -20,
    width: 200,
    height: 120,
    opacity: 0.35,
    overflow: 'hidden',
  },
  watermark: {
    width: '100%',
    height: '100%',
  },
  content: {
    padding: spacing.lg,
    zIndex: 1,
  },
  topRule: {
    alignSelf: 'center',
    width: 48,
    height: 3,
    borderRadius: 2,
    backgroundColor: colors.brandBronze,
    marginBottom: spacing.md,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  shieldSeal: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(156, 123, 92, 0.35)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  brandCopy: {
    alignItems: 'flex-start',
    flex: 1,
    maxWidth: 220,
  },
  brandName: {
    fontFamily: fontFamily.heading,
    fontSize: 18,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.2,
  },
  brandTagline: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.surfaceWhite,
    opacity: 0.75,
    marginTop: 2,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  meta: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '500',
    color: colors.brandBronzeLight,
    letterSpacing: 0.2,
  },
  metaDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.brandBronzeLight,
    opacity: 0.6,
  },
  previewNote: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    color: colors.surfaceWhite,
    opacity: 0.4,
    marginTop: spacing.md,
    textAlign: 'center',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
})
