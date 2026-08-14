"use client";

import { useState, useEffect } from "react";
import { dossiersService } from "@/services/dossiersService";
import { analystesService, Analyste } from "@/services/analystesService";
import { useAuthStore } from "@/store/authStore";
import { EtatChargement } from "@/components/ui/EtatChargement";
import MainLayout from "@/components/layout/MainLayout";

interface DossierValidation {
  id:                number;
  client_nom:        string;
  commercial_nom:    string;
  type_credit:       string;
  type_credit_display: string;
  montant_sollicite: number;
  duree_mois:        number;
  statut:            string;
  necessite_comite:  boolean;
  score:             number | null;
  niveau_risque:     string | null;
  decision_ia:       string | null;
  cree_le:           string;
}

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
  if (role === "CHEF_AGENCE" && statut === "SOUMIS")        return true;
  if (role === "ANALYSTE"    && statut === "EN_ANALYSE_1")  return true;
  return false;
};

interface ModalValidationProps {
  dossier:    DossierValidation;
  roleActuel: string | undefined;
  onFermer:   () => void;
  onValider:  (id: number, decision: string, commentaire: string, assigneA?: number) => Promise<void>;
}

function ModalValidation({ dossier, roleActuel, onFermer, onValider }: ModalValidationProps) {
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

        {/* En-tête modal */}
        <div className="flex items-center justify-between px-5 py-4
                        border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-800">
            Valider le dossier #{String(dossier.id).padStart(5, "0")}
          </h2>
          <button
            onClick={onFermer}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
              viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="p-5 space-y-4">

          {/* Résumé dossier */}
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
                <span className="text-xs font-medium px-2 py-0.5 rounded-full
                                 bg-pink-50 text-pink-600">
                  Requis
                </span>
              </div>
            )}
          </div>

          {/* Décision */}
          <div>
            <label className="block text-xs font-medium text-gray-500
                               uppercase tracking-wide mb-2">
              Votre décision *
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setDecision("APPROUVE")}
                className={`h-10 rounded-lg text-sm font-medium border transition-all
                            ${decision === "APPROUVE"
                              ? "border-green-500 bg-green-50 text-green-700"
                              : "border-gray-200 text-gray-500 hover:border-green-300"
                            }`}
              >
                Approuver
              </button>
              <button
                onClick={() => setDecision("REJETE")}
                className={`h-10 rounded-lg text-sm font-medium border transition-all
                            ${decision === "REJETE"
                              ? "border-red-400 bg-red-50 text-red-600"
                              : "border-gray-200 text-gray-500 hover:border-red-300"
                            }`}
              >
                Rejeter
              </button>
            </div>
          </div>

          {/* Sélection de l'analyste (1ère ou 2ème signature) */}
          {assignationRequise && (
            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-2">
                Assigner à l&apos;analyste *
              </label>
              {assignationRequise && (
                <div>
                  <label className="block text-xs font-medium text-gray-500
                                    uppercase tracking-wide mb-2">
                    Assigner à l&apos;analyste *
                  </label>
                  <select
                    value={analysteId}
                    onChange={(e) => setAnalysteId(e.target.value ? Number(e.target.value) : "")}
                    className="w-full h-10 border border-gray-200 rounded-lg px-3 text-sm
                              text-gray-700 bg-white focus:outline-none
                              focus:border-[#922b00] focus:ring-2 focus:ring-[#922b00]/10"
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
            </div>
          )}

          {/* Commentaire */}
          <div>
            <label className="block text-xs font-medium text-gray-500
                               uppercase tracking-wide mb-2">
              Commentaire
            </label>
            <textarea
              value={commentaire}
              onChange={(e) => setCommentaire(e.target.value)}
              rows={3}
              placeholder="Observations sur le dossier..."
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5
                         text-sm text-gray-700 placeholder:text-gray-400
                         focus:outline-none focus:border-[#922b00]
                         focus:ring-2 focus:ring-[#922b00]/10 resize-none"
            />
          </div>

          {erreur && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200
                          rounded px-3 py-2">
              {erreur}
            </p>
          )}

          {/* Boutons */}
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
              style={{ background: "#922b00" }}
            >
              {chargement ? "Enregistrement..." : "Confirmer"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ValidationPage() {
  const utilisateur = useAuthStore((s) => s.utilisateur);

  const [dossiers,           setDossiers]           = useState<DossierValidation[]>([]);
  const [chargement,         setChargement]         = useState(true);
  const [dossierSelectionne, setDossierSelectionne] = useState<DossierValidation | null>(null);

  const charger = async () => {
    try {
      const data  = await dossiersService.lister();
      const liste = (data.results || data) as DossierValidation[];
      setDossiers(liste);
    } catch {
      // Silencieux
    } finally {
      setChargement(false);
    }
  };

  useEffect(() => {
    charger();
  }, []);

  const handleValider = async (
    id:          number,
    decision:    string,
    commentaire: string,
    assigneA?:   number
  ) => {
    await dossiersService.valider(id, { decision, commentaire, assigne_a: assigneA });
    await charger();
    setDossierSelectionne(null);
  };

  const dossiersEnAttente = dossiers.filter(
    (d) => !["APPROUVE", "REJETE"].includes(d.statut)
  );

  const dossiersTraites = dossiers.filter(
    (d) => ["APPROUVE", "REJETE"].includes(d.statut)
  );

  return (
    <MainLayout titre="Validation des dossiers">
      <div className="space-y-5">

        {/* Dossiers en attente */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-50">
            <h2 className="text-sm font-semibold text-gray-800">
              En attente de validation
            </h2>
          </div>

          { chargement ? (
              <EtatChargement message="Chargement des dossiers..." />
            ) : dossiersEnAttente.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-gray-400">
                Aucun dossier en attente.
              </p>
            ) : (
              <div className="divide-y divide-gray-50">
                {dossiersEnAttente.map((d) => (
                  <div key={d.id}
                    className="px-5 py-4 flex items-center gap-4
                               hover:bg-gray-50/50 transition-colors">

                    <p className="text-xs font-mono text-gray-400 w-16 flex-shrink-0">
                      #{String(d.id).padStart(5, "0")}
                    </p>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {d.client_nom}
                      </p>
                      <p className="text-xs text-gray-400">
                        {d.commercial_nom} · {d.type_credit_display}
                      </p>
                    </div>

                    <p className="text-sm text-gray-700 w-36 flex-shrink-0 text-right">
                      {formaterMontant(d.montant_sollicite)}
                    </p>

                    {d.score !== null ? (
                      <span className={`text-xs font-medium px-2 py-1 rounded-full
                                        w-20 text-center flex-shrink-0
                                        ${COULEURS_RISQUE[d.niveau_risque ?? ""] ?? "text-gray-600 bg-gray-50"}`}>
                        {d.score}/100
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400 w-20 text-center flex-shrink-0">
                        —
                      </span>
                    )}

                    {d.decision_ia && (
                      <span className={`text-xs font-medium px-2 py-1 rounded-full
                                        flex-shrink-0 ${COULEURS_DECISION[d.decision_ia] ?? "text-gray-600 bg-gray-50"}`}>
                        {LABELS_DECISION[d.decision_ia] ?? d.decision_ia}
                      </span>
                    )}

                    {d.necessite_comite && (
                      <span className="text-[11px] font-medium px-2 py-1 rounded-full
                                       bg-pink-50 text-pink-600 flex-shrink-0">
                        Comité
                      </span>
                    )}

                    <button
                      onClick={() => setDossierSelectionne(d)}
                      className="h-8 px-3 rounded-lg text-xs font-medium text-white
                                 flex-shrink-0 transition-all hover:opacity-90"
                      style={{ background: "#922b00" }}
                    >
                      Valider
                    </button>
                  </div>
                ))}
              </div>
            )}
        </div>

        {/* Dossiers traités */}
        {dossiersTraites.length > 0 && (
          <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-50">
              <h2 className="text-sm font-semibold text-gray-800">
                Traités récemment
              </h2>
            </div>
            <div className="divide-y divide-gray-50">
              {dossiersTraites.map((d) => (
                <div key={d.id}
                  className="px-5 py-4 flex items-center gap-4">
                  <p className="text-xs font-mono text-gray-400 w-16 flex-shrink-0">
                    #{String(d.id).padStart(5, "0")}
                  </p>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {d.client_nom}
                    </p>
                    <p className="text-xs text-gray-400">{d.type_credit_display}</p>
                  </div>
                  <p className="text-sm text-gray-700 w-36 flex-shrink-0 text-right">
                    {formaterMontant(d.montant_sollicite)}
                  </p>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full
                                    flex-shrink-0
                                    ${d.statut === "APPROUVE"
                                      ? "bg-green-50 text-green-600"
                                      : "bg-red-50 text-red-600"
                                    }`}>
                    {d.statut === "APPROUVE" ? "Approuvé" : "Rejeté"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modal de validation */}
      {dossierSelectionne && (
        <ModalValidation
          dossier={dossierSelectionne}
          roleActuel={utilisateur?.role}
          onFermer={() => setDossierSelectionne(null)}
          onValider={handleValider}
        />
      )}
    </MainLayout>
  );
}