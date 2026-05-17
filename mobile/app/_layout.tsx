import { useEffect } from 'react'
import { Stack } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { StatusBar } from 'expo-status-bar'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { useAppFonts } from '@/hooks/useAppFonts'
import { brand } from '@/lib/brand'
import { colors, fontFamily } from '@/theme'

SplashScreen.preventAutoHideAsync()

export default function RootLayout() {
  const fontsLoaded = useAppFonts()

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync()
    }
  }, [fontsLoaded])

  if (!fontsLoaded) {
    return null
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.brandNavy },
          headerTintColor: colors.onNavy,
          headerTitleStyle: {
            fontFamily: fontFamily.heading,
            fontWeight: '600',
            fontSize: 17,
            color: colors.onNavy,
          },
          headerShadowVisible: true,
          contentStyle: { backgroundColor: colors.backgroundBase },
        }}
      >
        <Stack.Screen name="index" options={{ title: brand.name }} />
        <Stack.Screen name="ask" options={{ title: 'Ask a question' }} />
        <Stack.Screen name="scenarios" options={{ title: 'Scenario Guides' }} />
        <Stack.Screen name="about" options={{ title: 'About' }} />
      </Stack>
    </SafeAreaProvider>
  )
}
