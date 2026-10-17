import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  Pressable,
  Platform,
  TextInput,
  Modal,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import axios from 'axios';

// Динамическое определение URL бэкенда (для локалки или прода)
const getApiUrl = () => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      return '/api/v1';
    }
  }
  return 'http://127.0.0.1:8000/api/v1';
};

const API_URL = getApiUrl();

export default function App() {
  // Состояния для модалок
  const [authModalVisible, setAuthModalVisible] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  
  // Состояния формы
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [gender, setGender] = useState<'M' | 'F'>('M');
  const [loading, setLoading] = useState(false);

  // Состояние авторизованного юзера
  const [token, setToken] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<any>(null);

  // Открытие модалки Входа/Регистрации
  const openAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalVisible(true);
  };

  // Обработка отправки формы Входа / Регистрации
  const handleAuthSubmit = async () => {
    if (!email || !password) {
      alert('Заполните Email и пароль');
      return;
    }

    setLoading(true);

    try {
      if (authMode === 'register') {
        // 1. Регистрация
        await axios.post(`${API_URL}/users/register`, {
          email,
          password,
          first_name: firstName || 'Игрок',
          gender,
          preference: 'B',
        });
        alert('Регистрация успешна! Теперь войдите в аккаунт.');
        setAuthMode('login');
      } else {
        // 2. Логин
        const response = await axios.post(`${API_URL}/auth/login`, {
          email,
          password,
        });

        const accessToken = response.data.access_token;
        setToken(accessToken);

        // 3. Запрос профиля /me
        const meResponse = await axios.get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });

        setUserProfile(meResponse.data);
        setAuthModalVisible(false);
        alert(`С возвращением, ${meResponse.data.first_name}!`);
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Произошла ошибка при запросе к серверу';
      alert(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUserProfile(null);
  };

  return (
    <View style={styles.mainContainer}>
      <StatusBar style="light" />

      {/* ШАПКА СЕЙШЕНА (Header) */}
      <View style={styles.header}>
        <Text style={styles.logoText}>
          ZATUSIM<Text style={styles.logoDot}>.ONLINE</Text>
        </Text>

        <View style={styles.headerNav}>
          {userProfile ? (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <Text style={styles.userText}>🧑‍🚀 {userProfile.first_name}</Text>
              <Pressable style={styles.logoutBtn} onPress={handleLogout}>
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

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* HERO-СЕКЦИЯ */}
        <View style={styles.heroSection}>
          <LinearGradient
            colors={['#2c0a0a', '#4a1a1a', '#1a0a0a']}
            style={StyleSheet.absoluteFillObject}
          />
          <View style={styles.heroContent}>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>🔥 ХИТ СЕЗОНА 🔥</Text>
            </View>
            <Text style={styles.heroTitle}>ZATUSIM</Text>
            <Text style={styles.heroSubtitle}>Вечеринка начинается здесь</Text>
            <Text style={styles.heroDesc}>
              Забудь про скучные посиделки. Игры, задания, челленджи и безумные идеи — всё, чтобы твоя компания взорвалась от смеха.
            </Text>

            <View style={styles.heroButtons}>
              <Pressable style={styles.primaryBtn}>
                <Text style={styles.primaryBtnText}>Играть бесплатно 🎲</Text>
              </Pressable>
            </View>
          </View>
        </View>

        {/* СЕКЦИЯ РЕЖИМОВ ИГРЫ */}
        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>🎲 Как будем тусить?</Text>
          <View style={styles.cardsGrid}>
            <View style={styles.featureCard}>
              <Text style={styles.cardIcon}>🎯</Text>
              <Text style={styles.cardTitle}>Обычный режим</Text>
              <Text style={styles.cardDesc}>Сам выбирай: Правда или Действие. Честный ответ или безумный челлендж.</Text>
            </View>
            <View style={styles.featureCard}>
              <Text style={styles.cardIcon}>🎲</Text>
              <Text style={styles.cardTitle}>Рандом</Text>
              <Text style={styles.cardDesc}>Судьба решает за тебя. Случайное задание без права выбора!</Text>
            </View>
            <View style={styles.featureCard}>
              <Text style={styles.cardIcon}>⚖️</Text>
              <Text style={styles.cardTitle}>50 / 50</Text>
              <Text style={styles.cardDesc}>Идеальный баланс. Правда и Действие строго чередуются по кругу.</Text>
            </View>
          </View>
        </View>

        {/* ФУТЕР */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2026 ZATUSIM — Вселенная вечеринок</Text>
        </View>
      </ScrollView>

      {/* МОДАЛЬНОЕ ОКНО АВТОРИЗАЦИИ / РЕГИСТРАЦИИ */}
      <Modal visible={authModalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>
              {authMode === 'login' ? '🔑 Вход в Zatusim' : '🚀 Регистрация'}
            </Text>

            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor="#888"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <TextInput
              style={styles.input}
              placeholder="Пароль"
              placeholderTextColor="#888"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            {authMode === 'register' && (
              <>
                <TextInput
                  style={styles.input}
                  placeholder="Ваше Имя"
                  placeholderTextColor="#888"
                  value={firstName}
                  onChangeText={setFirstName}
                />
                <View style={{ flexDirection: 'row', gap: 10, marginBottom: 15 }}>
                  <Pressable
                    style={[styles.genderBtn, gender === 'M' && styles.genderBtnActive]}
                    onPress={() => setGender('M')}
                  >
                    <Text style={styles.genderBtnText}>👨 Парень</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.genderBtn, gender === 'F' && styles.genderBtnActive]}
                    onPress={() => setGender('F')}
                  >
                    <Text style={styles.genderBtnText}>👩 Девушка</Text>
                  </Pressable>
                </View>
              </>
            )}

            {loading ? (
              <ActivityIndicator size="large" color="#c1121f" style={{ marginVertical: 10 }} />
            ) : (
              <Pressable style={styles.submitBtn} onPress={handleAuthSubmit}>
                <Text style={styles.submitBtnText}>
                  {authMode === 'login' ? 'Войти' : 'Создать аккаунт'}
                </Text>
              </Pressable>
            )}

            <Pressable
              style={{ marginTop: 15 }}
              onPress={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
            >
              <Text style={{ color: '#c1121f', textAlign: 'center' }}>
                {authMode === 'login' ? 'Нет аккаунта? Зарегистрируйтесь' : 'Уже есть аккаунт? Войти'}
              </Text>
            </Pressable>

            <Pressable style={styles.closeBtn} onPress={() => setAuthModalVisible(false)}>
              <Text style={{ color: '#888', textAlign: 'center', marginTop: 10 }}>Закрыть</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  mainContainer: { flex: 1, backgroundColor: '#0d0d0d' },
  header: {
    paddingTop: Platform.OS === 'web' ? 15 : 45,
    paddingBottom: 15,
    paddingHorizontal: 20,
    backgroundColor: '#1a0a0a',
    borderBottomWidth: 2,
    borderBottomColor: '#c1121f',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logoText: { fontSize: 22, fontWeight: '900', color: '#fdf0d5', letterSpacing: 1 },
  logoDot: { color: '#c1121f' },
  headerNav: { flexDirection: 'row', gap: 10 },
  navBtn: { paddingVertical: 6, paddingHorizontal: 14, borderRadius: 20 },
  navBtnText: { color: '#fdf0d5', fontWeight: 'bold' },
  navBtnPrimary: { backgroundColor: '#c1121f', paddingVertical: 6, paddingHorizontal: 14, borderRadius: 20 },
  navBtnPrimaryText: { color: '#fff', fontWeight: 'bold' },
  userText: { color: '#fdf0d5', fontWeight: 'bold' },
  logoutBtn: { backgroundColor: '#3a0000', paddingVertical: 4, paddingHorizontal: 10, borderRadius: 12 },
  logoutBtnText: { color: '#ffaaaa', fontSize: 12 },

  scrollContent: { paddingBottom: 40 },
  heroSection: { padding: 30, alignItems: 'center', minHeight: 350, justifyContent: 'center', borderRadius: 20, margin: 15, overflow: 'hidden' },
  heroContent: { alignItems: 'center', maxWidth: 700 },
  badge: { backgroundColor: '#c1121f', paddingVertical: 4, paddingHorizontal: 12, borderRadius: 20, marginBottom: 15 },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  heroTitle: { fontSize: Platform.OS === 'web' ? 56 : 36, fontWeight: '900', color: '#fdf0d5', letterSpacing: 2 },
  heroSubtitle: { fontSize: 18, color: '#fdf0d5', marginBottom: 15 },
  heroDesc: { color: '#ffddcc', textAlign: 'center', fontSize: 15, lineHeight: 22, marginBottom: 25 },
  heroButtons: { flexDirection: 'row', gap: 15 },
  primaryBtn: { backgroundColor: '#c1121f', paddingVertical: 12, paddingHorizontal: 28, borderRadius: 30, borderWidth: 1, borderColor: '#ffcc00' },
  primaryBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },

  featuresSection: { padding: 20 },
  sectionTitle: { color: '#fdf0d5', fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 },
  cardsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 15, justifyContent: 'center' },
  featureCard: { backgroundColor: '#1a1a1a', borderWidth: 1, borderColor: '#333', borderRadius: 16, padding: 20, width: Platform.OS === 'web' ? 260 : '100%', alignItems: 'center' },
  cardIcon: { fontSize: 36, marginBottom: 10 },
  cardTitle: { color: '#fdf0d5', fontSize: 18, fontWeight: 'bold', marginBottom: 8 },
  cardDesc: { color: '#aaa', textAlign: 'center', fontSize: 13, lineHeight: 18 },

  footer: { padding: 20, borderTopWidth: 1, borderTopColor: '#222', marginTop: 30, alignItems: 'center' },
  footerText: { color: '#666', fontSize: 12 },

  // Модалка
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.8)', justifyContent: 'center', alignItems: 'center', padding: 20 },
  modalContent: { backgroundColor: '#1a1a1a', width: '100%', maxWidth: 400, borderRadius: 20, padding: 25, borderWidth: 1, borderColor: '#c1121f' },
  modalTitle: { color: '#fdf0d5', fontSize: 20, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  input: { backgroundColor: '#2a2a2a', color: '#fff', padding: 12, borderRadius: 10, marginBottom: 12, borderWidth: 1, borderColor: '#444' },
  genderBtn: { flex: 1, padding: 10, borderRadius: 10, borderWidth: 1, borderColor: '#444', alignItems: 'center' },
  genderBtnActive: { borderColor: '#c1121f', backgroundColor: 'rgba(193,18,31,0.2)' },
  genderBtnText: { color: '#fff' },
  submitBtn: { backgroundColor: '#c1121f', padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  submitBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  closeBtn: { marginTop: 10 },
});
