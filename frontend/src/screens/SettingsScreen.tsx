import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function SettingsScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>⚙️ Настройки</Text>
      <Text style={styles.subtitle}>
        Настройки приложения и уведомлений.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { color: '#fdf0d5', fontSize: 32, fontWeight: 'bold', marginBottom: 10 },
  subtitle: { color: '#aaa', fontSize: 16 },
});
