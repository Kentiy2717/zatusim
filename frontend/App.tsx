import React, { useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  Platform,
  ActivityIndicator,
  Text,
  Pressable,
  Image,
  ScrollView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import Sidebar, { AppRoute } from './src/components/Sidebar';
import AuthModal from './src/components/AuthModal';
import { getMediaUrl } from './src/api/client';

import PartiesScreen from './src/screens/PartiesScreen';
import GamesScreen from './src/screens/GamesScreen';
import RecipesScreen from './src/screens/RecipesScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import FriendsScreen from './src/screens/FriendsScreen';
import ChatScreen from './src/screens/ChatScreen';
import SettingsScreen from './src/screens/SettingsScreen';

const VALID_ROUTES: AppRoute[] = [
  'parties', 'games', 'recipes', 'profile', 'friends', 'chat', 'settings',
];

function getInitialRoute(): AppRoute {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const saved = window.localStorage.getItem('zatusim_route');
    if (saved && VALID_ROUTES.includes(saved as AppRoute)) {
      return saved as AppRoute;
    }
  }
  return 'parties';
}

function AppShell() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const [route, setRoute] = useState<AppRoute>(getInitialRoute);
  const [authVisible, setAuthVisible] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [isSidebarVisible, setSidebarVisible] = useState(
    Platform.OS === 'web' && typeof window !== 'undefined' ? window.innerWidth >= 900 : false,
  );

  // Сохраняем вкладку
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.localStorage.setItem('zatusim_route', route);
    }
  }, [route]);

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
    if (Platform.OS === 'web' && typeof window !== 'undefined' && window.innerWidth < 900) {
      setSidebarVisible(false);
    }
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

  const avatarUrl = getMediaUrl(user?.avatar_url ?? null);

  return (
    <View style={styles.root}>
      <StatusBar style="light" />

      {/* HEADER */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Pressable style={styles.menuBtn} onPress={() => setSidebarVisible((v) => !v)}>
            <Text style={styles.menuIcon}>☰</Text>
          </Pressable>
          <Pressable onPress={() => navigate('parties')}>
            <Text style={styles.logoText}>
              ZATUSIM<Text style={styles.logoDot}>.ONLINE</Text>
            </Text>
          </Pressable>
        </View>

        <View style={styles.headerNav}>
          {isAuthenticated && user ? (
            <View style={styles.userBlock}>
              <Pressable style={styles.userInfo} onPress={() => navigate('profile')}>
                {avatarUrl ? (
                  <Image source={{ uri: avatarUrl }} style={styles.headerAvatar} />
                ) : (
                  <View style={styles.headerAvatarPlaceholder}>
                    <Text style={{ fontSize: 14 }}>{user.gender === 'F' ? '👩' : '👨'}</Text>
                  </View>
                )}
                <View style={styles.userTextWrap}>
                  <Text style={styles.userUsername} numberOfLines={1}>
                    @{user.username}
                  </Text>
                  <Text style={styles.userName} numberOfLines={1}>
                    {user.first_name}{user.last_name ? ` ${user.last_name}` : ''}
                  </Text>
                </View>
              </Pressable>

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

      {/* LAYOUT: sidebar + scrollable content на всю ширину */}
      <View style={styles.layout}>
        {isSidebarVisible && <Sidebar current={route} onNavigate={navigate} />}

        <ScrollView
          style={styles.contentScroll}
          contentContainerStyle={styles.contentInner}
          // скроллбар у правого края окна
        >
          {content}
        </ScrollView>
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
  root: {
    flex: 1,
    backgroundColor: '#0d0d0d',
    ...(Platform.OS === 'web' ? { height: '100vh' as any, overflow: 'hidden' as any } : {}),
  },
  center: { justifyContent: 'center', alignItems: 'center' },

  header: {
    paddingTop: Platform.OS === 'web' ? 12 : 45,
    paddingBottom: 12,
    paddingHorizontal: 16,
    backgroundColor: '#140808',
    borderBottomWidth: 1,
    borderBottomColor: '#2a1010',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    zIndex: 10,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  menuBtn: { padding: 4 },
  menuIcon: { color: '#fdf0d5', fontSize: 24, fontWeight: 'bold' },
  logoText: { fontSize: 20, fontWeight: '900', color: '#fdf0d5', letterSpacing: 1 },
  logoDot: { color: '#c1121f' },

  headerNav: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  navBtn: { paddingVertical: 6, paddingHorizontal: 10, borderRadius: 20 },
  navBtnText: { color: '#fdf0d5', fontWeight: 'bold' },
  navBtnPrimary: { backgroundColor: '#c1121f', paddingVertical: 6, paddingHorizontal: 10, borderRadius: 20 },
  navBtnPrimaryText: { color: '#fff', fontWeight: 'bold' },

  userBlock: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  userInfo: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#c1121f',
  },
  headerAvatarPlaceholder: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  userTextWrap: { maxWidth: 160 },
  userUsername: { color: '#c1121f', fontWeight: 'bold', fontSize: 13 },
  userName: { color: '#aaa', fontSize: 11 },

  logoutBtn: {
    backgroundColor: '#3a0000',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  logoutBtnText: { color: '#ffaaaa', fontSize: 12, fontWeight: 'bold' },

  layout: { flex: 1, flexDirection: 'row' },

  // Scroll на всю оставшуюся ширину — полоса у края браузера
  contentScroll: {
    flex: 1,
  },
  contentInner: {
    padding: Platform.OS === 'web' ? 24 : 16,
    paddingBottom: 48,
    maxWidth: 1100,
    width: '100%',
    // НЕ alignSelf: 'center' — иначе скроллбар «прилипает» к контенту
  },
});
