import React from 'react';
import { View, Text, Pressable, StyleSheet, Platform } from 'react-native';
import { useAuth } from '../context/AuthContext';

export type AppRoute =
  | 'parties'
  | 'games'
  | 'recipes'
  | 'profile'
  | 'friends'
  | 'chat'
  | 'settings';

interface NavItem {
  key: AppRoute;
  label: string;
  icon: string;
  authOnly?: boolean;
}

const NAV: NavItem[] = [
  { key: 'profile', label: 'Моя страница', icon: '👤', authOnly: true },
  { key: 'friends', label: 'Друзья', icon: '👥', authOnly: true },
  { key: 'parties', label: 'Тусовки', icon: '🎉' },
  { key: 'games', label: 'Игры', icon: '🎮' },
  { key: 'recipes', label: 'Рецепты', icon: '🍳' },
  { key: 'chat', label: 'Чаты', icon: '💬', authOnly: true },
  { key: 'settings', label: 'Настройки', icon: '⚙️', authOnly: true },
];

interface Props {
  current: AppRoute;
  onNavigate: (route: AppRoute) => void;
}

export default function Sidebar({ current, onNavigate }: Props) {
  const { isAuthenticated } = useAuth();
  const items = NAV.filter((item) => !item.authOnly || isAuthenticated);

  return (
    <View style={styles.sidebar}>
      <View style={styles.nav}>
        {items.map((item) => {
          const active = current === item.key;
          return (
            <Pressable
              key={item.key}
              style={[styles.navItem, active && styles.navItemActive]}
              onPress={() => onNavigate(item.key)}
            >
              <Text style={styles.navIcon}>{item.icon}</Text>
              <Text style={[styles.navLabel, active && styles.navLabelActive]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  sidebar: {
    width: Platform.OS === 'web' ? 220 : 200,
    backgroundColor: '#140808',
    borderRightWidth: 1,
    borderRightColor: '#2a1010',
    paddingVertical: 15,
    paddingHorizontal: 10,
    minHeight: Platform.OS === 'web' ? ('100vh' as any) : undefined,
  },
  nav: { gap: 4 },
  navItem: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 10, paddingHorizontal: 10, borderRadius: 10 },
  navItemActive: { backgroundColor: 'rgba(193,18,31,0.25)' },
  navIcon: { fontSize: 18 },
  navLabel: { color: '#cbb', fontWeight: '600', fontSize: 14 },
  navLabelActive: { color: '#fdf0d5' },
});
