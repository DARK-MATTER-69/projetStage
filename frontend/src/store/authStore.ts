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
}

interface JwtPayload {
  user_id:  number;
  exp:      number;
}

interface AuthStore {
  accessToken:   string | null;
  refreshToken:  string | null;
  utilisateur:   Utilisateur | null;
  estConnecte:   boolean;

  // Actions
  connexion:     (access: string, refresh: string, utilisateur: Utilisateur) => void;
  deconnexion:   () => void;
  setUtilisateur:(utilisateur: Utilisateur) => void;
  tokenEstValide:() => boolean;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      accessToken:  null,
      refreshToken: null,
      utilisateur:  null,
      estConnecte:  false,

      connexion: (access, refresh, utilisateur) => {
        set({
          accessToken:  access,
          refreshToken: refresh,
          utilisateur,
          estConnecte:  true,
        });
      },

      deconnexion: () => {
        set({
          accessToken:  null,
          refreshToken: null,
          utilisateur:  null,
          estConnecte:  false,
        });
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
      name:    "sce-auth",
      partialize: (state) => ({
        accessToken:  state.accessToken,
        refreshToken: state.refreshToken,
        utilisateur:  state.utilisateur,
        estConnecte:  state.estConnecte,
      }),
    }
  )
);