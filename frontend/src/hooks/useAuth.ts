import { create } from 'zustand';
import { api } from '../api/client';

interface User {
  id: number;
  username: string;
  rol: string;
  activo: boolean;
  nombre_completo: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; message: string }>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  isLoading: false,
  login: async (username, password) => {
    set({ isLoading: true });
    try {
      const response = await api.post('/auth/login', { username, password });
      if (response.status_code === 200) {
        const token = response.data.access_token;
        localStorage.setItem('token', token);
        set({ token, isLoading: false });

        const userRes = await api.get('/auth/me');
        if (userRes.status_code === 200) {
          set({ user: userRes.data });
        }

        return { success: true, message: 'Bienvenido al sistema' };
      }
      return { success: false, message: response.message || 'Credenciales incorrectas' };
    } catch (error: any) {
      return { success: false, message: error.message || 'Error de conexión con el servidor' };
    } finally {
      set({ isLoading: false });
    }
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null });
  },
}));
