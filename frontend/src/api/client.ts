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

// Подставляем JWT из AsyncStorage в каждый запрос
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
  privacy_settings?: Record<string, boolean>;
}

export interface RegisterPayload {
  email: string;
  password: string;
  password_confirm: string;
  username: string;
  first_name: string;
  last_name?: string;
  gender: Gender;
  preference: Preference;
}

export interface LoginPayload {
  email: string;
  password: string;
}
