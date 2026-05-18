import {
  Inter_600SemiBold,
  useFonts,
} from '@expo-google-fonts/inter'
import { PublicSans_400Regular } from '@expo-google-fonts/public-sans'

export function useAppFonts(): boolean {
  const [loaded] = useFonts({
    Inter_600SemiBold,
    PublicSans_400Regular,
  })
  return loaded
}
