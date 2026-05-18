import { useEffect, useRef } from 'react'
import { Animated, StyleSheet, View } from 'react-native'
import { colors } from '@/theme'

const ORBIT_DOTS = 10

/** Glowing circuit orbit around the shield mark */
export function DigitalLogoOrbit({ diameter }: { diameter: number }) {
  const pulse = useRef(new Animated.Value(0.35)).current
  const radius = diameter / 2 - 6

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1400, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.35, duration: 1400, useNativeDriver: true }),
      ]),
    ).start()
  }, [pulse])

  return (
    <View style={[styles.wrap, { width: diameter, height: diameter }]} pointerEvents="none">
      {Array.from({ length: ORBIT_DOTS }).map((_, i) => {
        const angle = (i / ORBIT_DOTS) * Math.PI * 2 - Math.PI / 2
        const x = radius * Math.cos(angle) + diameter / 2 - 3
        const y = radius * Math.sin(angle) + diameter / 2 - 3
        return (
          <Animated.View
            key={i}
            style={[
              styles.dot,
              {
                left: x,
                top: y,
                opacity: pulse,
                transform: [{ scale: pulse }],
              },
            ]}
          />
        )
      })}
      <View style={[styles.ring, { width: diameter - 8, height: diameter - 8, borderRadius: (diameter - 8) / 2 }]} />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  ring: {
    position: 'absolute',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
    borderStyle: 'dashed',
  },
  dot: {
    position: 'absolute',
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.brandBronzeLight,
  },
})
