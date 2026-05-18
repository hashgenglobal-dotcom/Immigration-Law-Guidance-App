import { Image, StyleSheet, View } from 'react-native'
import { appImages } from '@/assets/images'
import { ImageFadeOverlay } from '@/components/ui/ImageFadeOverlay'
import { radii } from '@/theme'

export function DigitalHeroArt() {
  return (
    <View style={styles.wrap} pointerEvents="none">
      <Image source={appImages.heroAccent} style={styles.image} resizeMode="cover" />
      <ImageFadeOverlay variant="hero" />
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
})
