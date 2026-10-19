import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const getBaseUrl = () => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host !== 'localhost' && host !== '127.0.0.1') {
      return '/api/v1';
    }
  }
  return 'http://127.0.0.1:8000/api/v1';
};

export const api = axios.create({
  baseURL: getBaseUrl(),
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type Gender = 'M' | 'F';
export type Preference = 'M' | 'F' | 'B';
export type PartyStatus = 'ready' | 'busy' | 'snooze';

export interface PrivacySettings {
  show_first_name?: boolean;
  show_last_name?: boolean;
  show_birth_year?: boolean;
  show_preference?: boolean;
  show_city?: boolean;
  show_bio?: boolean;
  show_phone?: boolean;
  show_vk?: boolean;
  show_parties?: boolean;
  show_friends?: boolean;
}

export interface UserProfile {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string | null;
  gender: Gender;
  preference: Preference;
  avatar_url: string | null;
  bio: string | null;
  birth_date: string | null;
  city: string | null;
  phone: string | null;
  vk_link: string | null;
  party_status: PartyStatus;
  age?: number | null;
  is_adult?: boolean;
  privacy_settings?: PrivacySettings;
}

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  username: string;
  first_name: string;
  last_name?: string;
  birth_date: string;
  gender: Gender;
  preference: Preference;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UserUpdatePayload {
  email?: string;
  first_name?: string;
  last_name?: string | null;
  username?: string;
  city?: string | null;
  bio?: string | null;
  vk_link?: string | null;
  phone?: string | null;
  birth_date?: string | null;
  gender?: Gender;
  preference?: Preference;
  party_status?: PartyStatus;
  privacy_settings?: PrivacySettings;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

// ДОБАВИТЬ ЭТУ ФУНКЦИЮ В КОНЕЦ ФАЙЛА
export const getMediaUrl = (path: string | null) => {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  
  // Получаем базовый URL бэкенда (убираем /api/v1)
  const baseURL = api.defaults.baseURL as string; 
  const rootUrl = baseURL.replace('/api/v1', '');
  return `${rootUrl}${path}`;
};
