import api from "@/lib/axios";

export const scoringService = {

  /**
   * Récupère le score IA d'un dossier.
   */
  obtenirScore: async (dossierPk: number) => {
    const { data } = await api.get(`/api/scoring/${dossierPk}/`);
    return data;
  },
};