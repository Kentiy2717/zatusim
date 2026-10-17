import React, { useState } from 'react';
import { View, StyleSheet, Platform, ActivityIndicator, Text, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import Sidebar, { AppRoute } from './src/components/Sidebar';
import AuthModal from './src/components/AuthModal';

import PartiesScreen from './src/screens/PartiesScreen';
import GamesScreen from './src/screens/GamesScreen';
import RecipesScreen from './src/screens/RecipesScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import FriendsScreen from './src/screens/FriendsScreen';
import ChatScreen from './src/screens/ChatScreen';
import SettingsScreen from './src/screens/SettingsScreen';

function AppShell() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const [route, setRoute] = useState<AppRoute>('parties');
  const [authVisible, setAuthVisible] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const openAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthVisible(true);
  };

  const navigate = (next: AppRoute) => {
    const authOnly: AppRoute[] = ['profile', 'friends', 'chat', 'settings'];
    if (authOnly.includes(next) && !isAuthenticated) {
      openAuth('login');
      return;
    }
    setRoute(next);
  };

  if (isLoading) {
    return (
      <View style={[styles.root, styles.center]}>
        <ActivityIndicator size="large" color="#c1121f" />
      </View>
    );
  }

  const content = (() => {
    switch (route) {
      case 'games': return <GamesScreen />;
      case 'recipes': return <RecipesScreen />;
      case 'profile': return <ProfileScreen />;
      case 'friends': return <FriendsScreen />;
      case 'chat': return <ChatScreen />;
      case 'settings': return <SettingsScreen />;
      case 'parties':
      default: return <PartiesScreen />;
    }
  })();

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      
      {/* --- ШАПКА ВЕРХНЯЯ (Header) --- */}
      <View style={styles.header}>
        <Text style={styles.logoText}>
          ZATUSIM<Text style={styles.logoDot}>.ONLINE</Text>
        </Text>

        <View style={styles.headerNav}>
          {isAuthenticated && user ? (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <Text style={styles.userText}>🧑‍🚀 {user.first_name}</Text>
              <Pressable style={styles.logoutBtn} onPress={logout}>
                <Text style={styles.logoutBtnText}>Выйти</Text>
              </Pressable>
            </View>
          ) : (
            <>
              <Pressable style={styles.navBtn} onPress={() => openAuth('login')}>
                <Text style={styles.navBtnText}>Вход</Text>
              </Pressable>
              <Pressable style={styles.navBtnPrimary} onPress={() => openAuth('register')}>
                <Text style={styles.navBtnPrimaryText}>Регистрация</Text>
              </Pressable>
            </>
          )}
        </View>
      </View>

      {/* --- ОСНОВНОЙ КОНТЕНТ (Сайдбар + Экран) --- */}
      <View style={styles.layout}>
        <Sidebar current={route} onNavigate={navigate} />
        <View style={styles.content}>{content}</View>
      </View>

      <AuthModal
        visible={authVisible}
        mode={authMode}
        onClose={() => setAuthVisible(false)}
        onSwitchMode={setAuthMode}
      />
    </View>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#0d0d0d' },
  center: { justifyContent: 'center', alignItems: 'center' },
  
  // Стили верхней шапки
  header: {
    paddingTop: Platform.OS === 'web' ? 15 : 45,
    paddingBottom: 15,
    paddingHorizontal: 20,
    backgroundColor: '#140808',
    borderBottomWidth: 1,
    borderBottomColor: '#2a1010',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    zIndex: 10,
  },
  logoText: { fontSize: 22, fontWeight: '900', color: '#fdf0d5', letterSpacing: 1 },
  logoDot: { color: '#c1121f' },
  headerNav: { flexDirection: 'row', gap: 10, alignItems: 'center' },
  navBtn: { paddingVertical: 6, paddingHorizontal: 14, borderRadius: 20 },
  navBtnText: { color: '#fdf0d5', fontWeight: 'bold' },
  navBtnPrimary: { backgroundColor: '#c1121f', paddingVertical: 6, paddingHorizontal: 14, borderRadius: 20 },
  navBtnPrimaryText: { color: '#fff', fontWeight: 'bold' },
  userText: { color: '#fdf0d5', fontWeight: 'bold' },
  logoutBtn: { backgroundColor: '#3a0000', paddingVertical: 6, paddingHorizontal: 12, borderRadius: 12 },
  logoutBtnText: { color: '#ffaaaa', fontSize: 12, fontWeight: 'bold' },

  // Стили лейаута ВК
  layout: { flex: 1, flexDirection: 'row' },
  content: {
    flex: 1,
    padding: Platform.OS === 'web' ? 24 : 16,
    maxWidth: 1000,
  },
});
