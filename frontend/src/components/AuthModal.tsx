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
import { useAuth } from '../context/AuthContext';
import type { Gender, Preference } from '../api/client';

interface Props {
  visible: boolean;
  mode: 'login' | 'register';
  onClose: () => void;
  onSwitchMode: (mode: 'login' | 'register') => void;
}

export default function AuthModal({ visible, mode, onClose, onSwitchMode }: Props) {
  const { login, register } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [birthDate, setBirthDate] = useState(''); // <-- ДОБАВЛЕНО
  
  const [gender, setGender] = useState<Gender>('M');
  const [preference, setPreference] = useState<Preference>('F');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setError(null);
    setPassword('');
    setPasswordConfirm('');
  };

  const handleGenderSelect = (selectedGender: Gender) => {
    setGender(selectedGender);
    setPreference(selectedGender === 'M' ? 'F' : 'M');
  };

  const handleSubmit = async () => {
    setError(null);
    if (!email || !password) {
      setError('Заполните email и пароль');
      return;
    }
    if (mode === 'register') {
      if (!username || !firstName || !birthDate) {
        setError('Укажите никнейм, имя и дату рождения');
        return;
      }
      if (password !== passwordConfirm) {
        setError('Пароли не совпадают');
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === 'register') {
        await register({
          email,
          password,
          password_confirm: passwordConfirm,
          username,
          first_name: firstName,
          birth_date: birthDate, // <-- ОТПРАВЛЯЕМ НА БЭК
          gender,
          preference,
        });
        reset();
        onSwitchMode('login');
        setError('✅ Аккаунт создан. Теперь войдите.');
      } else {
        await login({ email, password });
        reset();
        onClose();
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Ошибка запроса к серверу');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.card}>
            <Text style={styles.title}>
              {mode === 'login' ? '🔑 Вход в Zatusim' : '🚀 Регистрация'}
            </Text>

            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor="#888"
              autoCapitalize="none"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />
            <TextInput
              style={styles.input}
              placeholder="Пароль"
              placeholderTextColor="#888"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />

            {mode === 'register' && (
              <>
                <TextInput
                  style={styles.input}
                  placeholder="Подтверждение пароля"
                  placeholderTextColor="#888"
                  secureTextEntry
                  value={passwordConfirm}
                  onChangeText={setPasswordConfirm}
                />
                <TextInput
                  style={styles.input}
                  placeholder="Никнейм (username)"
                  placeholderTextColor="#888"
                  autoCapitalize="none"
                  value={username}
                  onChangeText={setUsername}
                />
                <TextInput
                  style={styles.input}
                  placeholder="Имя"
                  placeholderTextColor="#888"
                  value={firstName}
                  onChangeText={setFirstName}
                />
                <Text style={styles.label}>Дата рождения</Text>
                {Platform.OS === 'web' ? (
                  // @ts-ignore — нативный HTML input type="date"
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
                      marginBottom: 10,
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

                <Text style={styles.label}>Пол</Text>
                <View style={styles.row}>
                  {([['M', '👨 Парень'], ['F', '👩 Девушка']] as const).map(([val, label]) => (
                    <Pressable
                      key={val}
                      style={[styles.chip, gender === val && styles.chipActive]}
                      onPress={() => handleGenderSelect(val)}
                    >
                      <Text style={styles.chipText}>{label}</Text>
                    </Pressable>
                  ))}
                </View>

                <Text style={styles.label}>Предпочтения (для игр)</Text>
                <View style={styles.row}>
                  {([['F', 'Девушки'], ['M', 'Парни'], ['B', 'Все']] as const).map(([val, label]) => (
                    <Pressable
                      key={val}
                      style={[styles.chip, preference === val && styles.chipActive]}
                      onPress={() => setPreference(val)}
                    >
                      <Text style={styles.chipText}>{label}</Text>
                    </Pressable>
                  ))}
                </View>
              </>
            )}

            {error && <Text style={[styles.error, error.includes('✅') && { color: '#4caf50' }]}>{error}</Text>}

            {loading ? (
              <ActivityIndicator color="#c1121f" style={{ marginVertical: 12 }} />
            ) : (
              <Pressable style={styles.submit} onPress={handleSubmit}>
                <Text style={styles.submitText}>
                  {mode === 'login' ? 'Войти' : 'Создать аккаунт'}
                </Text>
              </Pressable>
            )}

            <Pressable
              onPress={() => {
                setError(null);
                onSwitchMode(mode === 'login' ? 'register' : 'login');
              }}
              style={{ marginTop: 14 }}
            >
              <Text style={styles.switch}>
                {mode === 'login' ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
              </Text>
            </Pressable>

            <Pressable onPress={onClose}>
              <Text style={styles.close}>Закрыть</Text>
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
  card: { backgroundColor: '#1a1a1a', borderRadius: 20, padding: 24, borderWidth: 1, borderColor: '#c1121f', maxWidth: 420, width: '100%', alignSelf: 'center' },
  title: { color: '#fdf0d5', fontSize: 20, fontWeight: '800', textAlign: 'center', marginBottom: 18 },
  input: { backgroundColor: '#2a2a2a', color: '#fff', padding: 12, borderRadius: 10, marginBottom: 10, borderWidth: 1, borderColor: '#444' },
  label: { color: '#aaa', marginBottom: 6, marginTop: 4, fontSize: 13 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 10, borderWidth: 1, borderColor: '#444' },
  chipActive: { borderColor: '#c1121f', backgroundColor: 'rgba(193,18,31,0.25)' },
  chipText: { color: '#fff', fontSize: 13 },
  error: { color: '#ff8a8a', marginBottom: 8, textAlign: 'center' },
  submit: { backgroundColor: '#c1121f', padding: 14, borderRadius: 10, alignItems: 'center' },
  submitText: { color: '#fff', fontWeight: '800', fontSize: 16 },
  switch: { color: '#c1121f', textAlign: 'center' },
  close: { color: '#888', textAlign: 'center', marginTop: 12 },
});
