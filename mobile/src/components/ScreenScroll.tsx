import { ScrollView, StyleSheet, ViewStyle } from 'react-native'
import { colors, spacing } from '@/theme'

export function ScreenScroll({
  children,
  contentStyle,
}: {
  children: React.ReactNode
  contentStyle?: ViewStyle
}) {
  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={[styles.content, contentStyle]}
      keyboardShouldPersistTaps="handled"
    >
      {children}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
})
