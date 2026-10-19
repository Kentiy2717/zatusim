import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable, Platform, Image, ActivityIndicator, Linking } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { api, PartyStatus, getMediaUrl } from '../api/client';

import EditProfileModal from '../components/EditProfileModal';
import ChangePasswordModal from '../components/ChangePasswordModal';
import PrivacySettingsModal from '../components/PrivacySettingsModal';

export default function ProfileScreen() {
  const { user, refreshProfile } = useAuth();

  const [editVisible, setEditVisible] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [privacyVisible, setPrivacyVisible] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  if (!user) return null;

  const getPartyStatusUI = (status: PartyStatus) => {
    switch (status) {
      case 'ready': return { text: '🎉 Готов(а) тусить', color: '#4caf50' };
      case 'busy': return { text: '💼 Занят(а) делами', color: '#ff9800' };
      case 'snooze': return { text: '😴 Отдыхаю', color: '#9e9e9e' };
      default: return { text: status, color: '#aaa' };
    }
  };

  const partyUI = getPartyStatusUI(user.party_status);
  const avatarUrl = getMediaUrl(user.avatar_url);

  const handleAvatarUpload = () => {
    if (Platform.OS === 'web') {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async (e: any) => {
        const file = e.target?.files?.[0];
        if (!file) return;

        setUploadingAvatar(true);
        try {
          const formData = new FormData();
          formData.append('file', file);

          await api.post('/users/me/avatar', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          });
          await refreshProfile();
        } catch (err) {
          alert('Ошибка загрузки аватарки.');
        } finally {
          setUploadingAvatar(false);
        }
      };
      input.click();
    } else {
      alert('Загрузка поддерживается в веб-версии');
    }
  };

  const handleOpenVK = () => {
    if (user.vk_link) {
      let url = user.vk_link.trim();
      if (!url.startsWith('http')) url = 'https://' + url;
      Linking.openURL(url);
    }
  };

  return (
    <View style={styles.scrollContent}>
      <Text style={styles.screenTitle}>Моя страница</Text>

      <View style={styles.layout}>
        {/* ЛЕВАЯ КОЛОНКА */}
        <View style={styles.leftColumn}>
          <Pressable
            style={styles.avatarContainer}
            onPress={handleAvatarUpload}
            disabled={uploadingAvatar}
          >
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatar} />
            ) : (
              <View style={styles.avatarPlaceholder}>
                <Text style={styles.avatarEmoji}>{user.gender === 'F' ? '👩' : '👨'}</Text>
              </View>
            )}

            {uploadingAvatar && (
              <View style={styles.avatarLoadingOverlay}>
                <ActivityIndicator color="#fff" size="small" />
              </View>
            )}
          </Pressable>

          <Pressable style={styles.actionBtn} onPress={() => setEditVisible(true)}>
            <Text style={styles.actionBtnText}>✏️ Редактировать профиль</Text>
          </Pressable>
          
          <Pressable style={styles.secondaryBtn} onPress={() => setPasswordVisible(true)}>
            <Text style={styles.secondaryBtnText}>🔑 Изменить пароль</Text>
          </Pressable>

          <Pressable style={styles.secondaryBtn} onPress={() => setPrivacyVisible(true)}>
            <Text style={styles.secondaryBtnText}>👁️ Настройки приватности</Text>
          </Pressable>
        </View>

        {/* ПРАВАЯ КОЛОНКА */}
        <View style={styles.rightColumn}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                  <Text style={styles.fullName}>{user.first_name} {user.last_name || ''}</Text>
                  {user.is_adult && (
                    <View style={styles.badge18}><Text style={styles.badgeText}>18+</Text></View>
                  )}
                </View>
                <Text style={styles.username}>@{user.username}</Text>
              </View>
              
              <View style={[styles.statusBadge, { borderColor: partyUI.color }]}>
                <View style={[styles.statusDot, { backgroundColor: partyUI.color }]} />
                <Text style={[styles.statusText, { color: partyUI.color }]}>{partyUI.text}</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.infoGrid}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Возраст:</Text>
                <Text style={styles.infoValue}>{user.age !== null && user.age !== undefined ? `${user.age} лет` : 'Не указан'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Город:</Text>
                <Text style={styles.infoValue}>{user.city || 'Не указан'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Телефон:</Text>
                <Text style={styles.infoValue}>{user.phone || 'Не указан'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Кого ищу:</Text>
                <Text style={styles.infoValue}>{user.preference === 'F' ? 'Девушек' : user.preference === 'M' ? 'Парней' : 'Всех'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>VK:</Text>
                {user.vk_link ? (
                  <Pressable onPress={handleOpenVK}>
                    <Text style={[styles.infoValue, { color: '#4a76a8', textDecorationLine: 'underline' }]}>
                      {user.vk_link}
                    </Text>
                  </Pressable>
                ) : (
                  <Text style={[styles.infoValue, { color: '#666' }]}>Не привязан</Text>
                )}
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.bioSection}>
              <Text style={styles.bioTitle}>О себе:</Text>
              <Text style={styles.bioText}>{user.bio || 'Пользователь пока ничего не рассказал о себе.'}</Text>
            </View>

          </View>
        </View>
      </View>

      <EditProfileModal visible={editVisible} onClose={() => setEditVisible(false)} user={user} />
      <ChangePasswordModal visible={passwordVisible} onClose={() => setPasswordVisible(false)} />
      <PrivacySettingsModal visible={privacyVisible} onClose={() => setPrivacyVisible(false)} user={user} />
    </View>
  );
}

const styles = StyleSheet.create({
  scrollContent: { paddingBottom: 40 },
  screenTitle: { color: '#fdf0d5', fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  layout: { flexDirection: 'row', flexWrap: 'wrap', gap: 20, alignItems: 'flex-start' },
  leftColumn: { width: Platform.OS === 'web' ? 260 : '100%', gap: 12 },
  avatarContainer: { 
    backgroundColor: '#1a1a1a', 
    borderRadius: 16, 
    overflow: 'hidden', 
    borderWidth: 1, 
    borderColor: '#333', 
    aspectRatio: 1, 
    width: '100%', 
    position: 'relative',
    ...(Platform.OS === 'web' ? { cursor: 'pointer' as any } : {}),
  },
  avatar: { width: '100%', height: '100%' },
  avatarPlaceholder: { flex: 1, backgroundColor: '#2a2a2a', justifyContent: 'center', alignItems: 'center' },
  avatarEmoji: { fontSize: 80 },
  avatarLoadingOverlay: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(0,0,0,0.55)', justifyContent: 'center', alignItems: 'center' },
  actionBtn: { backgroundColor: '#c1121f', paddingVertical: 12, borderRadius: 12, alignItems: 'center' },
  actionBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  secondaryBtn: { backgroundColor: '#1a1a1a', paddingVertical: 12, borderRadius: 12, alignItems: 'center', borderWidth: 1, borderColor: '#333' },
  secondaryBtnText: { color: '#aaa', fontWeight: 'bold', fontSize: 14 },
  rightColumn: { flex: 1, minWidth: Platform.OS === 'web' ? 400 : '100%' },
  card: { backgroundColor: '#1a1a1a', borderRadius: 16, borderWidth: 1, borderColor: '#333', padding: 24 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 15 },
  fullName: { color: '#fdf0d5', fontSize: 26, fontWeight: '900' },
  username: { color: '#888', fontSize: 16, marginTop: 4 },
  badge18: { backgroundColor: '#c1121f', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, borderWidth: 1, backgroundColor: 'rgba(255,255,255,0.05)' },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusText: { fontWeight: 'bold', fontSize: 14 },
  divider: { height: 1, backgroundColor: '#333', marginVertical: 20 },
  infoGrid: { gap: 12 },
  infoRow: { flexDirection: 'row', alignItems: 'flex-start' },
  infoLabel: { color: '#888', width: 120, fontSize: 15 },
  infoValue: { color: '#fdf0d5', flex: 1, fontSize: 15, fontWeight: '500' },
  bioSection: { gap: 8 },
  bioTitle: { color: '#888', fontSize: 15 },
  bioText: { color: '#fdf0d5', fontSize: 15, lineHeight: 22 },
});
