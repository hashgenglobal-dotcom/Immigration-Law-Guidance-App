import { useState } from 'react'
import { StyleSheet, Text, View, TextInput } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, radii, shadows, spacing, typography } from '@/theme'

export function ScenarioSearchBar({
  value,
  onChangeText,
  placeholder = 'Search scenarios…',
}: {
  value: string
  onChangeText: (text: string) => void
  placeholder?: string
}) {
  const [focused, setFocused] = useState(false)

  return (
    <View style={[styles.wrap, focused && styles.wrapFocused]}>
      <View style={[styles.iconRing, focused && styles.iconRingFocused]}>
        <Ionicons
          name="search"
          size={18}
          color={focused ? colors.surfaceWhite : colors.brandNavy}
        />
      </View>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        clearButtonMode="while-editing"
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        returnKeyType="search"
      />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceWhite,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.12)',
    paddingRight: spacing.md,
    paddingLeft: spacing.xs,
    paddingVertical: spacing.xs,
    marginBottom: spacing.md,
    ...shadows.soft,
  },
  wrapFocused: {
    borderWidth: 2,
    borderColor: colors.brandNavy,
  },
  iconRing: {
    width: 40,
    height: 40,
    borderRadius: radii.button,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bronzeTint,
    marginRight: spacing.sm,
  },
  iconRingFocused: {
    backgroundColor: colors.brandNavy,
  },
  input: {
    flex: 1,
    fontSize: typography.small,
    fontFamily: fontFamily.body,
    color: colors.brandNavy,
    padding: 0,
    paddingVertical: spacing.sm,
  },
})
