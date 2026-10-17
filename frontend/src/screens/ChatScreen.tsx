import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function ChatScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>💬 Чаты</Text>
      <Text style={styles.subtitle}>
        Личные сообщения и чаты вечеринок.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { color: '#fdf0d5', fontSize: 32, fontWeight: 'bold', marginBottom: 10 },
  subtitle: { color: '#aaa', fontSize: 16 },
});
