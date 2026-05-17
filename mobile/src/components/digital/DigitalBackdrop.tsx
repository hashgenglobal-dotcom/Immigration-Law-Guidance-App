import { StyleSheet, View } from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { DotGrid } from './DotGrid'
import { colors } from '@/theme'

type BackdropVariant = 'home' | 'ask' | 'scenarios' | 'about'

const ORB_COLORS: Record<BackdropVariant, readonly [string, string, string, string]> = {
  home: ['rgba(31, 40, 57, 0.07)', 'transparent', 'rgba(156, 123, 92, 0.09)', 'transparent'],
  ask: ['rgba(156, 123, 92, 0.08)', 'transparent', 'rgba(31, 40, 57, 0.06)', 'transparent'],
  scenarios: ['rgba(31, 40, 57, 0.08)', 'transparent', 'rgba(156, 123, 92, 0.07)', 'transparent'],
  about: ['rgba(156, 123, 92, 0.07)', 'transparent', 'rgba(31, 40, 57, 0.05)', 'transparent'],
}

/** Soft gradient orbs + dot grid — adds depth without blocking touches */
export function DigitalBackdrop({ variant = 'home' }: { variant?: BackdropVariant }) {
  return (
    <View style={styles.root} pointerEvents="none">
      <LinearGradient
        colors={ORB_COLORS[variant]}
        locations={[0, 0.35, 0.65, 1]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      />
      <DotGrid opacity={0.14} />
      <View style={[styles.orb, styles.orbTop]} />
      <View style={[styles.orb, styles.orbBottom]} />
    </View>
  )
}

const styles = StyleSheet.create({
  root: {
    ...StyleSheet.absoluteFillObject,
    overflow: 'hidden',
    backgroundColor: colors.parchment,
  },
  gradient: {
    ...StyleSheet.absoluteFillObject,
    opacity: 0.9,
  },
  orb: {
    position: 'absolute',
    borderRadius: 999,
    backgroundColor: colors.brandNavy,
    opacity: 0.04,
  },
  orbTop: {
    width: 220,
    height: 220,
    top: -60,
    right: -40,
  },
  orbBottom: {
    width: 180,
    height: 180,
    bottom: 80,
    left: -50,
    backgroundColor: colors.brandBronze,
    opacity: 0.06,
  },
})
