import type { ReactNode } from 'react'
import { ScrollView, StyleSheet, View } from 'react-native'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import { DotGrid } from '@/components/digital/DotGrid'
import { NavyBackground } from '@/components/ui/NavyBackground'
import { colors, spacing } from '@/theme'

export function AuthShell({
  children,
  scroll = true,
}: {
  children: ReactNode
  scroll?: boolean
}) {
  const insets = useSafeAreaInsets()
  const body = (
    <View style={[styles.inner, { paddingTop: insets.top + spacing.md, paddingBottom: insets.bottom + spacing.lg }]}>
      {children}
    </View>
  )

  return (
    <View style={styles.root}>
      <NavyBackground />
      <DotGrid opacity={0.14} />
      {scroll ? (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {body}
        </ScrollView>
      ) : (
        body
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.brandNavy,
  },
  scrollContent: {
    flexGrow: 1,
  },
  inner: {
    flexGrow: 1,
    paddingHorizontal: spacing.lg,
  },
})
