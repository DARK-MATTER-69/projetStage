import api from "@/lib/axios";

export const clientsService = {

  /**
   * Récupère la liste des clients.
   */
  lister: async () => {
    const { data } = await api.get("/api/dossiers/clients/");
    return data;
  },

  /**
   * Récupère le détail d'un client.
   */
  detail: async (id: number) => {
    const { data } = await api.get(`/api/dossiers/clients/${id}/`);
    return data;
  },

  /**
   * Crée un nouveau client (Fiche 1).
   */
  creer: async (payload: {
    civilite:               string;
    nom:                    string;
    prenom:                 string;
    date_naissance:         string;
    lieu_naissance:         string;
    nationalite:            string;
    numero_cni:             string;
    telephone:              string;
    email:                  string;
    adresse:                string;
    type_employeur:         string;
    nom_employeur:          string;
    poste_occupe:           string;
    anciennete:             number;
    salaire_net:            number;
    charges_mensuelles:     number;
    credits_en_cours:       number;
    date_versement_salaire: number;
  }) => {
    const { data } = await api.post("/api/dossiers/clients/", payload);
    return data;
  },

  /**
   * Récupère l'historique des salaires d'un client.
   */
  historiqueSalaires: async (clientId: number) => {
    const { data } = await api.get(`/api/dossiers/clients/${clientId}/salaires/`);
    return data;
  },

  /**
   * Enregistre un nouveau salaire pour le client — met à jour son
   * salaire actuel et déclenche le recalcul des scores de ses
   * dossiers actifs.
   */
  ajouterSalaire: async (clientId: number, payload: {
    salaire:    number;
    date_effet: string;
    note?:      string;
  }) => {
    const { data } = await api.post(
      `/api/dossiers/clients/${clientId}/salaires/`,
      payload
    );
    return data;
  },

  /**
   * Récupère les impayés SCE d'un client.
   */
  impayes: async (clientId: number) => {
    const { data } = await api.get(`/api/dossiers/clients/${clientId}/impayes/`);
    return data;
  },

  /**
   * Enregistre un impayé pour un dossier du client.
   */
  ajouterImpaye: async (clientId: number, payload: {
    dossier_id:      number;
    montant_impaye:  number;
    date_echeance:   string;
    nb_mois_retard?: number;
  }) => {
    const { data } = await api.post(
      `/api/dossiers/clients/${clientId}/impayes/`,
      payload
    );
    return data;
  },

  /**
   * Régularise un impayé — déclenche le recalcul du score du dossier.
   */
  regulariserImpaye: async (impayeId: number) => {
    const { data } = await api.post(`/api/dossiers/impayes/${impayeId}/regulariser/`);
    return data;
  },

  /**
   * Recherche des clients existants par numéro CNI 
   */
  rechercherParCni: async (cni: string) => {
    try {
      const { data } = await api.get("/api/dossiers/clients/recherche/", {
        params: { cni },
      });
      return data as any[];
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } };
      if (error.response?.status === 404) return [];
      throw err;
    }
  },
};