import { Image, StyleSheet, View } from 'react-native'
import { appImages } from '@/assets/images'
import { LogoAppExplainer } from './LogoAppExplainer'
import { shadows, spacing } from '@/theme'

/** Torch + scales mark — app icon & welcome hero (squircle) */
export function SourcePathLogoMark({
  size = 96,
  showExplainer = false,
}: {
  size?: number
  showExplainer?: boolean
}) {
  const radius = Math.round(size * 0.223)

  return (
    <View style={styles.stack}>
      <View style={[styles.frame, { width: size, height: size, borderRadius: radius }]}>
        <Image
          source={appImages.logoIcon}
          style={{ width: size, height: size, borderRadius: radius }}
          resizeMode="cover"
          accessibilityLabel="SourcePath — immigration law guidance"
        />
      </View>
      {showExplainer ? <LogoAppExplainer /> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  stack: {
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  frame: {
    overflow: 'hidden',
    ...shadows.soft,
  },
})
