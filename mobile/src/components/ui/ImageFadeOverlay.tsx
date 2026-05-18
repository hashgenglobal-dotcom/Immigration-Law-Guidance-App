import { StyleSheet, View } from 'react-native'

type Props = {
  /** 'hero' = dark navy fade over hero art; 'light' = parchment wash; 'dark' = footer scrim */
  variant?: 'hero' | 'light' | 'dark'
}

/** Simulates gradient fade using stacked semi-transparent views */
export function ImageFadeOverlay({ variant = 'hero' }: Props) {
  if (variant === 'light') {
    return (
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <View style={[styles.layer, { backgroundColor: 'rgba(255,255,255,0.12)', top: 0, height: '35%' }]} />
        <View style={[styles.layer, { backgroundColor: 'rgba(244,241,234,0.75)', top: '30%', height: '40%' }]} />
        <View style={[styles.layer, { backgroundColor: 'rgba(244,241,234,0.95)', bottom: 0, height: '45%' }]} />
      </View>
    )
  }

  if (variant === 'dark') {
    return (
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <View style={[styles.layer, { backgroundColor: 'rgba(31,40,57,0.55)', top: 0, height: '40%' }]} />
        <View style={[styles.layer, { backgroundColor: 'rgba(31,40,57,0.88)', bottom: 0, height: '70%' }]} />
      </View>
    )
  }

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <View style={[styles.layer, { backgroundColor: 'transparent', top: 0, height: '25%' }]} />
      <View style={[styles.layer, { backgroundColor: 'rgba(31,40,57,0.45)', top: '25%', height: '35%' }]} />
      <View style={[styles.layer, { backgroundColor: 'rgba(31,40,57,0.88)', bottom: 0, height: '50%' }]} />
    </View>
  )
}

const styles = StyleSheet.create({
  layer: {
    position: 'absolute',
    left: 0,
    right: 0,
  },
})
