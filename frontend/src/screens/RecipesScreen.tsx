import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function RecipesScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🍳 Рецепты</Text>
      <Text style={styles.subtitle}>
        Коктейли, закуски и сеты для идеальной вечеринки.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { color: '#fdf0d5', fontSize: 32, fontWeight: 'bold', marginBottom: 10 },
  subtitle: { color: '#aaa', fontSize: 16 },
});
