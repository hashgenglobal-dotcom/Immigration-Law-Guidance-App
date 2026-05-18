import { useEffect, useRef } from 'react'
import { Animated, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { StatusBar } from 'expo-status-bar'
import { SourcePathLogoMark } from '@/components/brand/SourcePathLogoMark'
import { NavyBackground } from '@/components/ui/NavyBackground'
import { brand } from '@/lib/brand'
import { colors, fontFamily, radii, spacing } from '@/theme'

/** Branded loading screen — shown while fonts & auth hydrate (no hero image) */
export function SourcePathBootScreen() {
  const pulse = useRef(new Animated.Value(0.4)).current
  const rise = useRef(new Animated.Value(12)).current
  const fade = useRef(new Animated.Value(0)).current

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(rise, { toValue: 0, duration: 520, useNativeDriver: true }),
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulse, { toValue: 1, duration: 900, useNativeDriver: true }),
          Animated.timing(pulse, { toValue: 0.4, duration: 900, useNativeDriver: true }),
        ]),
      ),
    ]).start()
  }, [fade, pulse, rise])

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <NavyBackground />
      <View style={styles.mesh} pointerEvents="none">
        {Array.from({ length: 8 }).map((_, i) => (
          <View key={i} style={[styles.meshDot, { left: `${10 + i * 11}%` as `${number}%` }]} />
        ))}
      </View>

      <Animated.View
        style={[styles.content, { opacity: fade, transform: [{ translateY: rise }] }]}
      >
        <Animated.View style={[styles.logoWrap, { opacity: pulse }]}>
          <SourcePathLogoMark size={120} />
        </Animated.View>

        <Text style={styles.title}>{brand.name}</Text>
        <Text style={styles.tagline}>{brand.tagline}</Text>

        <View style={styles.mottoPill}>
          <Ionicons name="scale-outline" size={12} color={colors.brandBronzeLight} />
          <Text style={styles.motto}>{brand.motto}</Text>
        </View>

        <View style={styles.loaderRow}>
          <View style={styles.loaderTrack}>
            <Animated.View style={[styles.loaderFill, { opacity: pulse }]} />
          </View>
          <Text style={styles.loadingLabel}>Loading…</Text>
        </View>
      </Animated.View>
    </View>
  )
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.brandNavy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mesh: {
    ...StyleSheet.absoluteFillObject,
  },
  meshDot: {
    position: 'absolute',
    top: '18%',
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: colors.brandBronzeLight,
    opacity: 0.2,
  },
  content: {
    alignItems: 'center',
    paddingHorizontal: spacing.xl,
    width: '100%',
  },
  logoWrap: {
    marginBottom: spacing.lg,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 36,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.8,
    marginBottom: spacing.xs,
  },
  tagline: {
    fontFamily: fontFamily.body,
    fontSize: 16,
    color: colors.surfaceWhite,
    opacity: 0.88,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  mottoPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.full,
    backgroundColor: 'rgba(156, 123, 92, 0.22)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    marginBottom: spacing.xl,
  },
  motto: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: 0.3,
  },
  loaderRow: {
    width: '100%',
    maxWidth: 220,
    alignItems: 'center',
    gap: spacing.sm,
  },
  loaderTrack: {
    width: '100%',
    height: 3,
    borderRadius: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    overflow: 'hidden',
  },
  loaderFill: {
    width: '45%',
    height: '100%',
    borderRadius: 2,
    backgroundColor: colors.brandBronze,
  },
  loadingLabel: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '500',
    color: colors.brandBronzeLight,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
})
