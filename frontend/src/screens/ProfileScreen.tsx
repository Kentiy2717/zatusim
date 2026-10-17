import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAuth } from '../context/AuthContext';

export default function ProfileScreen() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>👤 Моя страница</Text>
      <View style={styles.card}>
        <Text style={styles.name}>
          {user.first_name} {user.last_name || ''}
        </Text>
        <Text style={styles.username}>@{user.username}</Text>
        <Text style={styles.info}>📧 Email: {user.email}</Text>
        <Text style={styles.info}>
          👤 Пол: {user.gender === 'M' ? 'Мужской' : 'Женский'}
        </Text>
        <Text style={styles.info}>🔥 Статус готовности: {user.party_status}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { color: '#fdf0d5', fontSize: 32, fontWeight: 'bold', marginBottom: 20 },
  card: {
    backgroundColor: '#1a1a1a',
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  name: { color: '#fdf0d5', fontSize: 24, fontWeight: 'bold' },
  username: { color: '#c1121f', fontSize: 16, marginBottom: 15 },
  info: { color: '#ccc', fontSize: 14, marginBottom: 8 },
});
