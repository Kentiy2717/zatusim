import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { api, PrivacySettings, UserProfile } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface Props {
  visible: boolean;
  onClose: () => void;
  user: UserProfile;
}

export default function PrivacySettingsModal({ visible, onClose, user }: Props) {
  const { refreshProfile } = useAuth();

  const [settings, setSettings] = useState<PrivacySettings>({
    show_first_name: user.privacy_settings?.show_first_name ?? true,
    show_last_name: user.privacy_settings?.show_last_name ?? true,
    show_birth_year: user.privacy_settings?.show_birth_year ?? true,
    show_preference: user.privacy_settings?.show_preference ?? true,
    show_city: user.privacy_settings?.show_city ?? true,
    show_bio: user.privacy_settings?.show_bio ?? true,
    show_phone: user.privacy_settings?.show_phone ?? false,
    show_vk: user.privacy_settings?.show_vk ?? true,
    show_parties: user.privacy_settings?.show_parties ?? true,
    show_friends: user.privacy_settings?.show_friends ?? true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (key: keyof PrivacySettings) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.patch('/users/me', { privacy_settings: settings });
      await refreshProfile();
      onClose();
    } catch (e: any) {
      setError('Ошибка сохранения настроек приватности');
    } finally {
      setLoading(false);
    }
  };

  const items: { key: keyof PrivacySettings; label: string }[] = [
    { key: 'show_first_name', label: 'Показывать имя' },
    { key: 'show_last_name', label: 'Показывать фамилию' },
    { key: 'show_birth_year', label: 'Показывать год рождения и возраст' },
    { key: 'show_preference', label: 'Показывать предпочтения' },
    { key: 'show_city', label: 'Показывать город' },
    { key: 'show_bio', label: 'Показывать раздел "О себе"' },
    { key: 'show_phone', label: 'Показывать телефон' },
    { key: 'show_vk', label: 'Показывать ссылку на VK' },
  ];

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.card}>
            <Text style={styles.title}>👁️ Настройки приватности</Text>
            <Text style={styles.subtitle}>Выберите, какие данные будут видны другим пользователям</Text>

            {items.map((item) => {
              const active = Boolean(settings[item.key]);
              return (
                <Pressable
                  key={item.key}
                  style={styles.row}
                  onPress={() => toggle(item.key)}
                >
                  <Text style={styles.label}>{item.label}</Text>
                  <View style={[styles.toggle, active && styles.toggleActive]}>
                    <Text style={styles.toggleText}>{active ? 'ВКЛ' : 'ВЫКЛ'}</Text>
                  </View>
                </Pressable>
              );
            })}

            {error && <Text style={styles.error}>{error}</Text>}

            {loading ? (
              <ActivityIndicator color="#c1121f" style={{ marginVertical: 12 }} />
            ) : (
              <Pressable style={styles.submit} onPress={handleSave}>
                <Text style={styles.submitText}>Сохранить</Text>
              </Pressable>
            )}

            <Pressable onPress={onClose} style={{ marginTop: 12 }}>
              <Text style={styles.close}>Отмена</Text>
            </Pressable>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'center' },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: '#c1121f',
    maxWidth: 440,
    width: '100%',
    alignSelf: 'center',
  },
  title: { color: '#fdf0d5', fontSize: 20, fontWeight: '800', textAlign: 'center', marginBottom: 4 },
  subtitle: { color: '#888', fontSize: 13, textAlign: 'center', marginBottom: 18 },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  label: { color: '#ccc', fontSize: 14, flex: 1, marginRight: 10 },
  toggle: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
    backgroundColor: '#333',
  },
  toggleActive: { backgroundColor: '#c1121f' },
  toggleText: { color: '#fff', fontSize: 12, fontWeight: 'bold' },
  error: { color: '#ff8a8a', marginTop: 10, textAlign: 'center' },
  submit: { backgroundColor: '#c1121f', padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 16 },
  submitText: { color: '#fff', fontWeight: '800', fontSize: 16 },
  close: { color: '#888', textAlign: 'center' },
});
