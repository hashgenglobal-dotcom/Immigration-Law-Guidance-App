import { Image, StyleSheet, View } from 'react-native'
import type { ImageSourcePropType } from 'react-native'
import { radii } from '@/theme'

export function IllustrationBanner({
  source,
  height = 120,
}: {
  source: ImageSourcePropType
  height?: number
}) {
  return (
    <View style={[styles.wrap, { height }]}>
      <Image source={source} style={styles.image} resizeMode="cover" accessibilityIgnoresInvertColors />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
    borderRadius: radii.card,
    overflow: 'hidden',
    marginBottom: 12,
  },
  image: {
    width: '100%',
    height: '100%',
  },
})
