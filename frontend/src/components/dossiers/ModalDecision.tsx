"use client";

import { useState, useEffect } from "react";
import { analystesService, Analyste } from "@/services/analystesService";

const COULEURS_RISQUE: Record<string, string> = {
  FAIBLE:   "text-green-600 bg-green-50",
  MOYEN:    "text-orange-600 bg-orange-50",
  ELEVE:    "text-red-600 bg-red-50",
  CRITIQUE: "text-red-800 bg-red-100",
};

const COULEURS_DECISION: Record<string, string> = {
  FAVORABLE:    "text-green-600 bg-green-50",
  CONDITIONNEL: "text-orange-600 bg-orange-50",
  DEFAVORABLE:  "text-red-600 bg-red-50",
};

const LABELS_DECISION: Record<string, string> = {
  FAVORABLE:    "Favorable",
  CONDITIONNEL: "Conditionnel",
  DEFAVORABLE:  "Défavorable",
};

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

/**
 * Détermine si la décision de l'utilisateur connecté sur ce dossier
 * nécessite l'assignation d'un analyste (1er ou 2ème signataire).
 */
const requiertAssignation = (role: string | undefined, statut: string) => {
  if (role === "CHEF_AGENCE_COMMERCIALE" && statut === "SOUMIS")     return true;
  if (role === "ANALYSTE"                && statut === "EN_ANALYSE_1") return true;
  return false;
};

export interface DossierPourDecision {
  id:                number;
  client_nom:        string;
  montant_sollicite: number;
  statut:            string;
  necessite_comite:  boolean;
  score:             number | null;
  niveau_risque:     string | null;
  decision_ia:       string | null;
}

interface ModalDecisionProps {
  dossier:    DossierPourDecision;
  roleActuel: string | undefined;
  onFermer:   () => void;
  onValider:  (id: number, decision: string, commentaire: string, assigneA?: number) => Promise<void>;
}

export default function ModalDecision({ dossier, roleActuel, onFermer, onValider }: ModalDecisionProps) {
  const [decision,    setDecision]    = useState("");
  const [commentaire, setCommentaire] = useState("");
  const [analystes,   setAnalystes]   = useState<Analyste[]>([]);
  const [analysteId,  setAnalysteId]  = useState<number | "">("");
  const [chargement,  setChargement]  = useState(false);
  const [erreur,      setErreur]      = useState("");

  const assignationRequise = decision === "APPROUVE" &&
    requiertAssignation(roleActuel, dossier.statut);

  useEffect(() => {
    if (!assignationRequise) return;
    analystesService.lister()
      .then(setAnalystes)
      .catch(() => setAnalystes([]));
  }, [assignationRequise]);

  const handleSubmit = async () => {
    if (!decision) return;
    if (assignationRequise && !analysteId) {
      setErreur("Vous devez sélectionner un analyste.");
      return;
    }

    setChargement(true);
    setErreur("");
    try {
      await onValider(
        dossier.id,
        decision,
        commentaire,
        assignationRequise ? Number(analysteId) : undefined
      );
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setErreur(error.response?.data?.detail || "Une erreur est survenue.");
      setChargement(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center
                    justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md">

        <div className="flex items-center justify-between px-5 py-4
                        border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-800">
            Valider le dossier #{String(dossier.id).padStart(5, "0")}
          </h2>
          <button onClick={onFermer} className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
              viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="p-5 space-y-4">

          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Client</span>
              <span className="font-medium text-gray-800">{dossier.client_nom}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Montant</span>
              <span className="font-medium text-gray-800">
                {formaterMontant(dossier.montant_sollicite)}
              </span>
            </div>
            {dossier.score !== null && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Score IA</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full
                                  ${COULEURS_RISQUE[dossier.niveau_risque ?? ""] ?? "text-gray-600 bg-gray-50"}`}>
                  {dossier.score}/100
                </span>
              </div>
            )}
            {dossier.decision_ia && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Décision IA</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full
                                  ${COULEURS_DECISION[dossier.decision_ia] ?? "text-gray-600 bg-gray-50"}`}>
                  {LABELS_DECISION[dossier.decision_ia] ?? dossier.decision_ia}
                </span>
              </div>
            )}
            {dossier.necessite_comite && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Comité</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-pink-50 text-pink-600">
                  Requis
                </span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              Votre décision *
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setDecision("APPROUVE")}
                className={`h-10 rounded-lg text-sm font-medium border transition-all
                            ${decision === "APPROUVE"
                              ? "border-green-500 bg-green-50 text-green-700"
                              : "border-gray-200 text-gray-500 hover:border-green-300"}`}
              >
                Approuver
              </button>
              <button
                onClick={() => setDecision("REJETE")}
                className={`h-10 rounded-lg text-sm font-medium border transition-all
                            ${decision === "REJETE"
                              ? "border-red-400 bg-red-50 text-red-600"
                              : "border-gray-200 text-gray-500 hover:border-red-300"}`}
              >
                Rejeter
              </button>
            </div>
          </div>

          {assignationRequise && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Assigner à l&apos;analyste *
              </label>
              <select
                value={analysteId}
                onChange={(e) => setAnalysteId(e.target.value ? Number(e.target.value) : "")}
                className="w-full h-10 border border-gray-200 rounded-lg px-3 text-sm
                          text-gray-700 bg-white focus:outline-none
                          focus:border-[var(--color-brand)] focus:ring-2 focus:ring-[var(--color-brand)]/10"
              >
                <option value="">Sélectionner un analyste</option>
                {analystes.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.nom} — {a.disponible
                      ? "Libre"
                      : `${a.dossiers_en_cours} dossier${a.dossiers_en_cours > 1 ? "s" : ""} en cours`}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              Commentaire
            </label>
            <textarea
              value={commentaire}
              onChange={(e) => setCommentaire(e.target.value)}
              rows={3}
              placeholder="Observations sur le dossier..."
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5
                         text-sm text-gray-700 placeholder:text-gray-400
                         focus:outline-none focus:border-[var(--color-brand)]
                         focus:ring-2 focus:ring-[var(--color-brand)]/10 resize-none"
            />
          </div>

          {erreur && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {erreur}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              onClick={onFermer}
              className="flex-1 h-10 border border-gray-200 rounded-lg
                         text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSubmit}
              disabled={!decision || chargement}
              className="flex-1 h-10 rounded-lg text-sm font-medium
                         text-white disabled:opacity-50 transition-all"
              style={{ background: "var(--color-brand)" }}
            >
              {chargement ? "Enregistrement..." : "Confirmer"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}