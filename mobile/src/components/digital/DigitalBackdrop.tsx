import { StyleSheet, View } from 'react-native'
import { DotGrid } from './DotGrid'
import { colors } from '@/theme'

type BackdropVariant = 'home' | 'ask' | 'scenarios' | 'about'

/** Soft orbs + dot grid — adds depth without native gradients */
export function DigitalBackdrop({ variant = 'home' }: { variant?: BackdropVariant }) {
  const bronzeTint = variant === 'ask' ? 0.09 : 0.07
  const navyTint = variant === 'scenarios' ? 0.08 : 0.06

  return (
    <View style={styles.root} pointerEvents="none">
      <View style={[styles.wash, { backgroundColor: `rgba(156, 123, 92, ${bronzeTint})` }]} />
      <View style={[styles.washBottom, { backgroundColor: `rgba(31, 40, 57, ${navyTint})` }]} />
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
  wash: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '45%',
  },
  washBottom: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '40%',
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
