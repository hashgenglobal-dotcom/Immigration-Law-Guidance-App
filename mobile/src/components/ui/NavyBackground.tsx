import { StyleSheet, View } from 'react-native'
import { colors } from '@/theme'

/** Layered navy background — no native gradient module required */
export function NavyBackground() {
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <View style={styles.base} />
      <View style={styles.topGlow} />
      <View style={styles.bottomGlow} />
    </View>
  )
}

const styles = StyleSheet.create({
  base: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.brandNavy,
  },
  topGlow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '38%',
    backgroundColor: '#151B27',
    opacity: 0.55,
  },
  bottomGlow: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '42%',
    backgroundColor: '#243044',
    opacity: 0.45,
  },
})
