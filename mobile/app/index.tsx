import { ActivityIndicator, StyleSheet, View } from 'react-native'
import { Redirect } from 'expo-router'
import { useAuth } from '@/context/AuthContext'
import { colors } from '@/theme'

/** Entry gate — routes to welcome, auth choice, or main app */
export default function RootIndex() {
  const { isReady, session, onboardingComplete } = useAuth()

  if (!isReady) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.brandBronze} />
      </View>
    )
  }

  if (!session) {
    if (!onboardingComplete) {
      return <Redirect href="/(auth)/welcome" />
    }
    return <Redirect href="/(auth)/choice" />
  }

  return <Redirect href="/(main)" />
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.brandNavy,
  },
})
