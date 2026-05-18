import { useEffect } from 'react'
import { Stack } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { StatusBar } from 'expo-status-bar'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { SourcePathBootScreen } from '@/components/boot/SourcePathBootScreen'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { useAppFonts } from '@/hooks/useAppFonts'

SplashScreen.preventAutoHideAsync()

function RootNavigator() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen
        name="(main)"
        options={{
          headerShown: false,
          gestureEnabled: false,
        }}
      />
    </Stack>
  )
}

function AppShell() {
  const fontsLoaded = useAppFonts()
  const { isReady } = useAuth()

  useEffect(() => {
    if (fontsLoaded && isReady) {
      SplashScreen.hideAsync()
    }
  }, [fontsLoaded, isReady])

  if (!fontsLoaded || !isReady) {
    return <SourcePathBootScreen />
  }

  return (
    <>
      <StatusBar style="light" />
      <RootNavigator />
    </>
  )
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </SafeAreaProvider>
  )
}
