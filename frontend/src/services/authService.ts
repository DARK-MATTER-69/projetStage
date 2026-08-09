import api from "@/lib/axios";

export const authService = {

  /**
   * Connexion et récupération des tokens JWT.
   */
  login: async (username: string, password: string) => {
    const { data } = await api.post("/api/auth/login/", { username, password });
    return data;
  },

  /**
   * Récupère le profil de l'utilisateur connecté.
   */
  profil: async () => {
    const { data } = await api.get("/api/auth/profil/");
    return data;
  },

  /**
   * Met à jour le profil de l'utilisateur connecté.
   */
  modifierProfil: async (payload: {
    first_name?: string;
    last_name?:  string;
    email?:      string;
    telephone?:  string;
  }) => {
    const { data } = await api.put("/api/auth/profil/modifier/", payload);
    return data;
  },

  /**
   * Change le mot de passe de l'utilisateur connecté.
   */
  changerMotDePasse: async (
    ancienMotDePasse:  string,
    nouveauMotDePasse: string
  ) => {
    const { data } = await api.post("/api/auth/mot-de-passe/modifier/", {
      ancien_mot_de_passe:  ancienMotDePasse,
      nouveau_mot_de_passe: nouveauMotDePasse,
    });
    return data;
  },
};