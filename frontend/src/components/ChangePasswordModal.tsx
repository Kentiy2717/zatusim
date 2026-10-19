import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { api } from '../api/client';

interface Props {
  visible: boolean;
  onClose: () => void;
}

export default function ChangePasswordModal({ visible, onClose }: Props) {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const reset = () => {
    setOldPassword('');
    setNewPassword('');
    setNewPasswordConfirm('');
    setError(null);
    setSuccess(false);
  };

  const handleSubmit = async () => {
    setError(null);
    if (!oldPassword || !newPassword || !newPasswordConfirm) {
      setError('Заполните все поля');
      return;
    }

    if (newPassword !== newPasswordConfirm) {
      setError('Новые пароли не совпадают');
      return;
    }

    if (newPassword.length < 8) {
      setError('Длина пароля должна быть не менее 8 символов');
      return;
    }

    setLoading(true);
    try {
      await api.post('/users/me/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });

      setSuccess(true);
      setTimeout(() => {
        reset();
        onClose();
      }, 1500);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Ошибка смены пароля');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.title}>🔑 Изменение пароля</Text>

          {success ? (
            <Text style={styles.success}>✅ Пароль успешно изменён!</Text>
          ) : (
            <>
              <TextInput
                style={styles.input}
                placeholder="Текущий пароль"
                placeholderTextColor="#888"
                secureTextEntry
                value={oldPassword}
                onChangeText={setOldPassword}
              />
              <TextInput
                style={styles.input}
                placeholder="Новый пароль"
                placeholderTextColor="#888"
                secureTextEntry
                value={newPassword}
                onChangeText={setNewPassword}
              />
              <TextInput
                style={styles.input}
                placeholder="Подтверждение нового пароля"
                placeholderTextColor="#888"
                secureTextEntry
                value={newPasswordConfirm}
                onChangeText={setNewPasswordConfirm}
              />

              {error && <Text style={styles.error}>{error}</Text>}

              {loading ? (
                <ActivityIndicator color="#c1121f" style={{ marginVertical: 12 }} />
              ) : (
                <Pressable style={styles.submit} onPress={handleSubmit}>
                  <Text style={styles.submitText}>Обновить пароль</Text>
                </Pressable>
              )}
            </>
          )}

          <Pressable
            onPress={() => {
              reset();
              onClose();
            }}
            style={{ marginTop: 14 }}
          >
            <Text style={styles.close}>Закрыть</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'center', padding: 20 },
  card: {
    backgroundColor: '#1a1a1a',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: '#c1121f',
    maxWidth: 400,
    width: '100%',
    alignSelf: 'center',
  },
  title: { color: '#fdf0d5', fontSize: 20, fontWeight: '800', textAlign: 'center', marginBottom: 18 },
  input: {
    backgroundColor: '#2a2a2a',
    color: '#fff',
    padding: 12,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#444',
  },
  error: { color: '#ff8a8a', marginBottom: 8, textAlign: 'center' },
  success: { color: '#4caf50', fontSize: 16, fontWeight: 'bold', textAlign: 'center', marginVertical: 20 },
  submit: { backgroundColor: '#c1121f', padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  submitText: { color: '#fff', fontWeight: '800', fontSize: 16 },
  close: { color: '#888', textAlign: 'center' },
});
