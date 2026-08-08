import axios from "axios";
import { useAuthStore } from "@/store/authStore";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
});

/**
 * Intercepteur de requête :
 * Ajoute automatiquement le token JWT dans chaque requête sortante.
 */
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Intercepteur de réponse :
 * Si le serveur retourne 401, on déconnecte l'utilisateur.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().deconnexion();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;