import api from "@/lib/axios";

export interface NotificationItem {
  id:         number;
  message:    string;
  dossier_id: number | null;
  cree_le:    string;
}

export const notificationsService = {
  /**
   * Récupère les notifications non lues de l'utilisateur connecté.
   */
  lister: async (): Promise<NotificationItem[]> => {
    const { data } = await api.get("/api/dossiers/notifications/");
    return data;
  },

  /**
   * Marque une notification comme lue.
   */
  marquerLue: async (id: number) => {
    const { data } = await api.post(`/api/dossiers/notifications/${id}/lue/`);
    return data;
  },
};