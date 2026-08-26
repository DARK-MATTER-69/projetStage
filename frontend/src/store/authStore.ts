import { create } from "zustand";
import { persist } from "zustand/middleware";
import { jwtDecode } from "jwt-decode";

interface Utilisateur {
  id:         number;
  username:   string;
  first_name: string;
  last_name:  string;
  email:      string;
  role:       string;
  agence:     string;
  telephone:  string;
}

interface JwtPayload {
  user_id: number;
  exp:     number;
}

interface AuthStore {
  accessToken:    string | null;
  refreshToken:   string | null;
  utilisateur:    Utilisateur | null;
  estConnecte:    boolean;
  connexion:      (access: string, refresh: string, utilisateur: Utilisateur) => void;
  deconnexion:    () => void;
  mettreAJourAccessToken: (access: string) => void;
  setUtilisateur: (utilisateur: Utilisateur) => void;
  tokenEstValide: () => boolean;
}

/** Stocke le token dans un cookie accessible par le middleware */
const setCookie = (name: string, value: string, days = 1) => {
  if (typeof document === "undefined") return;
  const expires = new Date();
  expires.setDate(expires.getDate() + days);
  document.cookie = `${name}=${value}; path=/; expires=${expires.toUTCString()}`;
};

/** Supprime un cookie */
const deleteCookie = (name: string) => {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      accessToken:  null,
      refreshToken: null,
      utilisateur:  null,
      estConnecte:  false,

      connexion: (access, refresh, utilisateur) => {
        // Stocker dans le cookie pour le middleware
        setCookie("access_token", access, 1/3);
        setCookie("user_role", utilisateur.role, 1);
        set({
          accessToken:  access,
          refreshToken: refresh,
          utilisateur,
          estConnecte:  true,
        });
      },

      deconnexion: () => {
        deleteCookie("access_token");
        deleteCookie("user_role");
        set({
          accessToken:  null,
          refreshToken: null,
          utilisateur:  null,
          estConnecte:  false,
        });
      },

      mettreAJourAccessToken: (access) => {
        setCookie("access_token", access, 1/3);
        set({ accessToken: access });
      },

      setUtilisateur: (utilisateur) => set({ utilisateur }),

      tokenEstValide: () => {
        const token = get().accessToken;
        if (!token) return false;
        try {
          const decoded = jwtDecode<JwtPayload>(token);
          return decoded.exp * 1000 > Date.now();
        } catch {
          return false;
        }
      },
    }),
    {
      name: "sce-auth",
      partialize: (state) => ({
        accessToken:  state.accessToken,
        refreshToken: state.refreshToken,
        utilisateur:  state.utilisateur,
        estConnecte:  state.estConnecte,
      }),
    }
  )
);