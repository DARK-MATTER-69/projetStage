import api from "@/lib/axios";

export const adminService = {

  /**
   * Récupère la liste de tous les utilisateurs.
   * Réservé à l'administrateur.
   */
  listerUtilisateurs: async () => {
    const { data } = await api.get("/api/auth/utilisateurs/");
    return data;
  },

  /**
   * Crée un nouvel utilisateur.
   */
  creerUtilisateur: async (payload: {
    username:   string;
    first_name: string;
    last_name:  string;
    email:      string;
    role:       string;
    agence:     string;
    telephone:  string;
    password:   string;
  }) => {
    const { data } = await api.post("/api/auth/utilisateurs/", payload);
    return data;
  },

  /**
   * Met à jour un utilisateur.
   */
  modifierUtilisateur: async (id: number, payload: {
    first_name?: string;
    last_name?:  string;
    email?:      string;
    role?:       string;
    agence?:     string;
    telephone?:  string;
    is_active?:  boolean;
  }) => {
    const { data } = await api.patch(`/api/auth/utilisateurs/${id}/`, payload);
    return data;
  },
};