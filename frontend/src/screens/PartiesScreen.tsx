import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function PartiesScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🎉 Тусовки</Text>
      <Text style={styles.subtitle}>
        Главная страница. Здесь будут отображаться актуальные тусовки и события рядом с тобой.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { color: '#fdf0d5', fontSize: 32, fontWeight: 'bold', marginBottom: 10 },
  subtitle: { color: '#aaa', fontSize: 16 },
});
