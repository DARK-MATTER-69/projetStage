"use client";

import { useState, useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import { dossiersService } from "@/services/dossiersService";
import { analystesService, Analyste } from "@/services/analystesService";
import { EtatChargement, EtatErreur } from "@/components/ui/EtatChargement";
import JaugeScore from "@/components/ui/JaugeScore";

interface DossierAnalyse {
  id:                  number;
  client_nom:          string;
  commercial_nom:      string;
  type_credit_display: string;
  montant_sollicite:   number;
  duree_mois:          number;
  statut:              string;
  statut_display:      string;
  necessite_comite:    boolean;
  cree_le:             string;
  score:               number | null;
  niveau_risque:       string;
  decision_ia:         string | null;
}

const COULEURS_RISQUE: Record<string, string> = {
  FAIBLE:   "text-green-600 bg-green-50",
  MOYEN:    "text-orange-600 bg-orange-50",
  ELEVE:    "text-red-600 bg-red-50",
  CRITIQUE: "text-red-800 bg-red-100",
};

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

interface ModalAnalyseProps {
  dossier:   DossierAnalyse;
  onFermer:  () => void;
  onValide:  () => void;
}

function ModalAnalyse({ dossier, onFermer, onValide }: ModalAnalyseProps) {
  const [decision,    setDecision]    = useState("");
  const [commentaire, setCommentaire] = useState("");
  const [analystes,   setAnalystes]   = useState<Analyste[]>([]);
  const [analysteId,  setAnalysteId]  = useState<number | "">("");
  const [chargement,  setChargement]  = useState(false);
  const [erreur,      setErreur]      = useState("");

  // La 1ère étape d'analyse (EN_ANALYSE_1) exige d'assigner un 2ème
  // analyste ; la 2ème étape (EN_ANALYSE_2) clôt directement l'analyse.
  const necessiteAssignation = decision === "APPROUVE" && dossier.statut === "EN_ANALYSE_1";

  useEffect(() => {
    if (!necessiteAssignation) return;
    analystesService.lister().then(setAnalystes).catch(() => setAnalystes([]));
  }, [necessiteAssignation]);

  const handleSubmit = async () => {
    if (!decision) return;
    if (necessiteAssignation && !analysteId) {
      setErreur("Vous devez sélectionner le 2ème analyste.");
      return;
    }

    setChargement(true);
    setErreur("");
    try {
      await dossiersService.valider(dossier.id, {
        decision,
        commentaire,
        assigne_a: necessiteAssignation ? Number(analysteId) : undefined,
      });
      onValide();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setErreur(error.response?.data?.detail || "Une erreur est survenue.");
      setChargement(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-800">
            Analyser le dossier #{String(dossier.id).padStart(5, "0")}
          </h2>
          <button onClick={onFermer} className="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
              viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Client</span>
              <span className="font-medium text-gray-800">{dossier.client_nom}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Montant</span>
              <span className="font-medium text-gray-800">{formaterMontant(dossier.montant_sollicite)}</span>
            </div>
            {dossier.score !== null && (
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Score IA</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${COULEURS_RISQUE[dossier.niveau_risque] ?? "text-gray-600 bg-gray-50"}`}>
                  {dossier.score}/100 — {dossier.niveau_risque}
                </span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              Votre avis *
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setDecision("APPROUVE")}
                className={`h-10 rounded-lg text-sm font-medium border transition-all
                            ${decision === "APPROUVE" ? "border-green-500 bg-green-50 text-green-700" : "border-gray-200 text-gray-500 hover:border-green-300"}`}
              >
                Favorable
              </button>
              <button
                onClick={() => setDecision("REJETE")}
                className={`h-10 rounded-lg text-sm font-medium border transition-all
                            ${decision === "REJETE" ? "border-red-400 bg-red-50 text-red-600" : "border-gray-200 text-gray-500 hover:border-red-300"}`}
              >
                Défavorable
              </button>
            </div>
          </div>

          {necessiteAssignation && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Assigner au 2ème analyste *
              </label>
              <select
                value={analysteId}
                onChange={(e) => setAnalysteId(e.target.value ? Number(e.target.value) : "")}
                className="w-full h-10 border border-gray-200 rounded-lg px-3 text-sm bg-white
                           focus:outline-none focus:border-[#922b00] focus:ring-2 focus:ring-[#922b00]/10"
              >
                <option value="">Sélectionner un analyste</option>
                {analystes.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.nom} — {a.disponible ? "Libre" : `${a.dossiers_en_cours} dossier(s) en cours`}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
              Commentaire / avis motivé
            </label>
            <textarea
              value={commentaire}
              onChange={(e) => setCommentaire(e.target.value)}
              rows={4}
              placeholder="Observations sur le dossier..."
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm
                         placeholder:text-gray-400 focus:outline-none focus:border-[#922b00]
                         focus:ring-2 focus:ring-[#922b00]/10 resize-none"
            />
          </div>

          {erreur && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {erreur}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button onClick={onFermer}
              className="flex-1 h-10 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
              Annuler
            </button>
            <button
              onClick={handleSubmit}
              disabled={!decision || chargement}
              className="flex-1 h-10 rounded-lg text-sm font-medium text-white disabled:opacity-50"
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

export default function AnalysePage() {
  const [dossiers,           setDossiers]           = useState<DossierAnalyse[]>([]);
  const [chargement,         setChargement]         = useState(true);
  const [erreur,             setErreur]             = useState("");
  const [dossierSelectionne, setDossierSelectionne] = useState<DossierAnalyse | null>(null);

  const charger = async () => {
    try {
      const data = await dossiersService.lister();
      setDossiers(data.results || data);
    } catch {
      setErreur("Impossible de charger les dossiers.");
    } finally {
      setChargement(false);
    }
  };

  useEffect(() => { charger(); }, []);

  return (
    <MainLayout titre="Dossiers à analyser">
      <div className="space-y-5">
        <div className="bg-white border border-gray-100 rounded-xl px-5 py-4 flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ background: "rgba(146,43,0,0.08)" }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
              viewBox="0 0 24 24" fill="none" stroke="#922b00"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-800">Dossiers assignés à votre analyse</p>
            <p className="text-xs text-gray-400 mt-0.5">
              Consultez le score IA et rendez votre avis motivé sur chaque dossier.
            </p>
          </div>
        </div>

        {chargement ? (
          <EtatChargement message="Chargement des dossiers..." />
        ) : erreur ? (
          <EtatErreur message={erreur} />
        ) : dossiers.length === 0 ? (
          <div className="bg-white border border-gray-100 rounded-xl py-16 text-center">
            <p className="text-sm text-gray-400">Aucun dossier en attente d'analyse.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {dossiers.map((d) => (
              <div key={d.id} className="bg-white border border-gray-100 rounded-xl p-5 hover:border-gray-200 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-xs font-mono text-gray-400">#{String(d.id).padStart(5, "0")}</span>
                      <span className="text-sm font-semibold text-gray-800">{d.client_nom}</span>
                      {d.necessite_comite && (
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-pink-50 text-pink-600">
                          Comité requis
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Type</p>
                        <p className="text-sm text-gray-700">{d.type_credit_display}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Montant</p>
                        <p className="text-sm text-gray-700 font-medium">{formaterMontant(d.montant_sollicite)}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Durée</p>
                        <p className="text-sm text-gray-700">{d.duree_mois} mois</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-0.5">Commercial</p>
                        <p className="text-sm text-gray-700">{d.commercial_nom}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    {d.score !== null ? (
                      <JaugeScore score={Number(d.score)} niveauRisque={String(d.niveau_risque ?? "")} taille={72} />
                    ) : (
                      <div className="text-center w-16">
                        <p className="text-xs text-gray-400">Score N/A</p>
                      </div>
                    )}

                    <button
                      onClick={() => setDossierSelectionne(d)}
                      className="h-9 px-4 rounded-lg text-sm font-medium text-white transition-all hover:opacity-90"
                      style={{ background: "#922b00" }}
                    >
                      Analyser
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {dossierSelectionne && (
        <ModalAnalyse
          dossier={dossierSelectionne}
          onFermer={() => setDossierSelectionne(null)}
          onValide={() => {
            setDossierSelectionne(null);
            charger();
          }}
        />
      )}
    </MainLayout>
  );
}