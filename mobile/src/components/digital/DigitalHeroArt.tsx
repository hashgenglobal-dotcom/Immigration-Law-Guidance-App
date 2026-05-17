import { Image, StyleSheet, View } from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { appImages } from '@/assets/images'
import { radii } from '@/theme'

export function DigitalHeroArt() {
  return (
    <View style={styles.wrap} pointerEvents="none">
      <Image source={appImages.heroAccent} style={styles.image} resizeMode="cover" />
      <LinearGradient
        colors={['transparent', 'rgba(31, 40, 57, 0.55)', 'rgba(31, 40, 57, 0.92)']}
        locations={[0.2, 0.55, 1]}
        style={styles.fade}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: radii.card,
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
    opacity: 0.55,
  },
  fade: {
    ...StyleSheet.absoluteFillObject,
  },
})
