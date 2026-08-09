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
};