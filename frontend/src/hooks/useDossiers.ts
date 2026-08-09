import { useState, useEffect, useCallback } from "react";
import { dossiersService } from "@/services/dossiersService";

/**
 * Hook pour récupérer et gérer la liste des dossiers.
 */
export function useDossiers(params?: { statut?: string }) {
  const [dossiers,    setDossiers]    = useState<unknown[]>([]);
  const [chargement,  setChargement]  = useState(true);
  const [erreur,      setErreur]      = useState("");

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur("");
    try {
      const data = await dossiersService.lister(params);
      setDossiers(data.results || data);
    } catch {
      setErreur("Impossible de charger les dossiers.");
    } finally {
      setChargement(false);
    }
  }, []);

  useEffect(() => { charger(); }, [charger]);

  return { dossiers, chargement, erreur, recharger: charger };
}

/**
 * Hook pour récupérer le détail d'un dossier.
 */
export function useDossierDetail(id: number) {
  const [dossier,    setDossier]    = useState<unknown>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur,     setErreur]     = useState("");

  useEffect(() => {
    const charger = async () => {
      setChargement(true);
      setErreur("");
      try {
        const data = await dossiersService.detail(id);
        setDossier(data);
      } catch {
        setErreur("Dossier introuvable.");
      } finally {
        setChargement(false);
      }
    };
    if (id) charger();
  }, [id]);

  return { dossier, chargement, erreur };
}