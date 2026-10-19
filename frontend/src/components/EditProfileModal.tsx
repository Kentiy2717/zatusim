import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  Platform,
} from 'react-native';
import { api, UserProfile, UserUpdatePayload, PartyStatus, Preference } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface Props {
  visible: boolean;
  onClose: () => void;
  user: UserProfile;
}

export default function EditProfileModal({ visible, onClose, user }: Props) {
  const { refreshProfile } = useAuth();

  const [email, setEmail] = useState(user.email || '');
  const [username, setUsername] = useState(user.username || '');
  const [firstName, setFirstName] = useState(user.first_name || '');
  const [lastName, setLastName] = useState(user.last_name || '');
  const [birthDate, setBirthDate] = useState(user.birth_date || '');
  const [city, setCity] = useState(user.city || '');
  const [phone, setPhone] = useState(user.phone || '');
  const [bio, setBio] = useState(user.bio || '');
  const [vkLink, setVkLink] = useState(user.vk_link || '');
  const [partyStatus, setPartyStatus] = useState<PartyStatus>(user.party_status || 'ready');
  const [preference, setPreference] = useState<Preference>(user.preference || 'F');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    if (!firstName.trim() || !username.trim() || !email.trim()) {
      setError('Email, никнейм и имя обязательны');
      return;
    }

    setLoading(true);
    try {
      const payload: UserUpdatePayload = {
        email: email.trim(),
        username: username.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim() || null,
        birth_date: birthDate || null,
        city: city.trim() || null,
        phone: phone.trim() || null,
        bio: bio.trim() || null,
        vk_link: vkLink.trim() || null,
        party_status: partyStatus,
        preference,
      };

      await api.patch('/users/me', payload);
      await refreshProfile();
      onClose();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Ошибка обновления профиля');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.card}>
            <Text style={styles.title}>✏️ Редактирование профиля</Text>

            <Text style={styles.label}>Email</Text>
            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor="#888"
              autoCapitalize="none"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />

            <View style={styles.rowInputs}>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Никнейм</Text>
                <TextInput
                  style={styles.input}
                  placeholder="username"
                  placeholderTextColor="#888"
                  autoCapitalize="none"
                  value={username}
                  onChangeText={setUsername}
                />
              </View>

              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Дата рождения</Text>
                {Platform.OS === 'web' ? (
                  // @ts-ignore
                  <input
                    type="date"
                    value={birthDate}
                    onChange={(e: any) => setBirthDate(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    style={{
                      backgroundColor: '#2a2a2a',
                      color: '#fff',
                      padding: 12,
                      borderRadius: 10,
                      marginBottom: 8,
                      border: '1px solid #444',
                      width: '100%',
                      fontSize: 14,
                      outline: 'none',
                      colorScheme: 'dark',
                      boxSizing: 'border-box',
                    }}
                  />
                ) : (
                  <TextInput
                    style={styles.input}
                    placeholder="ГГГГ-ММ-ДД"
                    placeholderTextColor="#888"
                    value={birthDate}
                    onChangeText={setBirthDate}
                  />
                )}
              </View>
            </View>

            <View style={styles.rowInputs}>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Имя</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Имя"
                  placeholderTextColor="#888"
                  value={firstName}
                  onChangeText={setFirstName}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Фамилия</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Фамилия"
                  placeholderTextColor="#888"
                  value={lastName}
                  onChangeText={setLastName}
                />
              </View>
            </View>

            <View style={styles.rowInputs}>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Город</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Томск"
                  placeholderTextColor="#888"
                  value={city}
                  onChangeText={setCity}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.label}>Телефон</Text>
                <TextInput
                  style={styles.input}
                  placeholder="+7..."
                  placeholderTextColor="#888"
                  value={phone}
                  onChangeText={setPhone}
                  keyboardType="phone-pad"
                />
              </View>
            </View>

            <Text style={styles.label}>Ссылка ВКонтакте</Text>
            <TextInput
              style={styles.input}
              placeholder="https://vk.com/..."
              placeholderTextColor="#888"
              value={vkLink}
              onChangeText={setVkLink}
            />

            <Text style={styles.label}>Статус готовности</Text>
            <View style={styles.row}>
              {([
                ['ready', '🎉 Готов(а)'],
                ['busy', '💼 Занят(а)'],
                ['snooze', '😴 Отдыхаю'],
              ] as const).map(([val, label]) => (
                <Pressable
                  key={val}
                  style={[styles.chip, partyStatus === val && styles.chipActive]}
                  onPress={() => setPartyStatus(val)}
                >
                  <Text style={styles.chipText}>{label}</Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.label}>Кого ищете</Text>
            <View style={styles.row}>
              {([
                ['F', 'Девушки'],
                ['M', 'Парни'],
                ['B', 'Все'],
              ] as const).map(([val, label]) => (
                <Pressable
                  key={val}
                  style={[styles.chip, preference === val && styles.chipActive]}
                  onPress={() => setPreference(val)}
                >
                  <Text style={styles.chipText}>{label}</Text>
                </Pressable>
              ))}
            </View>

            <Text style={styles.label}>О себе</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Расскажите о себе..."
              placeholderTextColor="#888"
              multiline
              numberOfLines={4}
              value={bio}
              onChangeText={setBio}
            />

            {error && <Text style={styles.error}>{error}</Text>}

            {loading ? (
              <ActivityIndicator color="#c1121f" style={{ marginVertical: 12 }} />
            ) : (
              <Pressable style={styles.submit} onPress={handleSubmit}>
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
    maxWidth: 480,
    width: '100%',
    alignSelf: 'center',
  },
  title: { color: '#fdf0d5', fontSize: 20, fontWeight: '800', textAlign: 'center', marginBottom: 16 },
  label: { color: '#aaa', fontSize: 13, marginBottom: 4, marginTop: 6 },
  input: {
    backgroundColor: '#2a2a2a',
    color: '#fff',
    padding: 12,
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#444',
  },
  rowInputs: { flexDirection: 'row', gap: 10 },
  textArea: { height: 90, textAlignVertical: 'top' },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 10, borderWidth: 1, borderColor: '#444' },
  chipActive: { borderColor: '#c1121f', backgroundColor: 'rgba(193,18,31,0.25)' },
  chipText: { color: '#fff', fontSize: 13 },
  error: { color: '#ff8a8a', marginBottom: 8, textAlign: 'center' },
  submit: { backgroundColor: '#c1121f', padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  submitText: { color: '#fff', fontWeight: '800', fontSize: 16 },
  close: { color: '#888', textAlign: 'center' },
});
