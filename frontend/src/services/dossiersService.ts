import api from "@/lib/axios";

export const dossiersService = {

  /**
   * Récupère la liste des dossiers de l'utilisateur connecté.
   */
  lister: async (params?: { statut?: string; necessite_comite?: boolean }) => {
    const { data } = await api.get("/api/dossiers/", { params });
    return data;
  },

  /**
   * Récupère le détail d'un dossier par son ID.
   */
  detail: async (id: number) => {
    const { data } = await api.get(`/api/dossiers/${id}/`);
    return data;
  },

  /**
   * Crée un nouveau dossier.
   */
  creer: async (payload: {
    client_id:              number;
    type_credit:            string;
    montant_sollicite:      number;
    duree_mois:             number;
    objet_financement:      string;
    appreciation:           string;
    date_debut_prelevement: string;
    jour_prelevement:       number;
    echeance_mens_banque:  number;
    encours_sce:           number;
    assureur:              string;
    montant_assurance_ttc: number;
    avi:                   boolean;
    delegation_salaire:    boolean;
  }) => {
    const { data } = await api.post("/api/dossiers/", payload);
    return data;
  },

  /**
   * Soumet un dossier au chef d'agence.
   * Déclenche le calcul du score IA.
   */
  soumettre: async (id: number) => {
    const { data } = await api.post(`/api/dossiers/${id}/soumettre/`);
    return data;
  },

  /**
   * Enregistre une décision de validation sur un dossier.
   */
  valider: async (id: number, payload: {
    decision:    string;
    commentaire: string;
    assigne_a?:  number;
  }) => {
    const { data } = await api.post(`/api/dossiers/${id}/valider/`, payload);
    return data;
  },

  /**
   * Récupère l'historique personnel des décisions prises
   * par l'utilisateur connecté (chef d'agence, analyste, direction, comité).
   */
  historique: async () => {
    const { data } = await api.get("/api/dossiers/historique/");
    return data;
  },
  
  /**
   * Recalcule manuellement le score d'un dossier
   * (ex : après modification des infos client hors salaire).
   */
  recalculer: async (id: number) => {
    const { data } = await api.post(`/api/dossiers/${id}/recalculer/`);
    return data;
  },

  /**
   * Upload un document pour un dossier.
   */
  uploaderDocument: async (id: number, typeDocument: string, fichier: File) => {
    const formData = new FormData();
    formData.append("type_document", typeDocument);
    formData.append("fichier", fichier);
    const { data } = await api.post(
      `/api/dossiers/${id}/documents/`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data;
  },

    /**
   * Supprime un dossier en brouillon.
   */
  supprimer: async (id: number) => {
    await api.delete(`/api/dossiers/${id}/supprimer/`);
  },
};