import api from "@/lib/axios";

export interface Analyste {
  id:                 number;
  nom:                string;
  dossiers_en_cours:  number;
  disponible:         boolean;
}

export const analystesService = {
  /**
   * Récupère la liste des analystes avec leur charge de travail,
   * pour assignation d'un dossier.
   */
  lister: async (): Promise<Analyste[]> => {
    const { data } = await api.get("/api/auth/utilisateurs/analystes/");
    return data;
  },
};