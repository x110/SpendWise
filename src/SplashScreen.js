import React, { useEffect } from 'react';
import { View, StyleSheet, Animated, Image } from 'react-native';

const SplashScreen = ({ navigation }) => {
  const scaleAnim = new Animated.Value(1); // Start scale at 1

  useEffect(() => {
    // Define the scale up and down animations
    const scaleUp = Animated.timing(scaleAnim, {
      toValue: 1.5, // Scale up to 1.5 times the original size
      duration: 1500,
      useNativeDriver: true,
    });

    const scaleDown = Animated.timing(scaleAnim, {
      toValue: 1, // Scale back to the original size
      duration: 2000,
      useNativeDriver: true,
    });

    // Run the animations in a loop
    Animated.loop(
      Animated.sequence([scaleUp, scaleDown])
    ).start();

    // Navigate to the main screen after 5 seconds
    setTimeout(() => {
      navigation.replace('Home'); // Replace 'Home' with your main screen name
    }, 5000); // Duration must match the animation duration

  }, [scaleAnim, navigation]);

  return (
    <View style={styles.container}>
      <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
        <Image source={require('../assets/logo.png')} style={styles.logo} />
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'white',
  },
  logo: {
    width: 150,
    height: 150,
    borderRadius: 80, // Adjusted to fit logo nicely
  },
})

export default SplashScreen;
