"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { dossiersService } from "@/services/dossiersService";
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

export default function AnalysePage() {
  const [dossiers,    setDossiers]    = useState<DossierAnalyse[]>([]);
  const [chargement,  setChargement]  = useState(true);
  const [erreur,      setErreur]      = useState("");

  useEffect(() => {
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
    charger();
  }, []);

  return (
    <MainLayout titre="Dossiers à analyser">
      <div className="space-y-5">

        {/* En-tête informatif */}
        <div className="bg-white border border-gray-100 rounded-xl px-5 py-4
                        flex items-center gap-3">
          <div className="p-2 rounded-lg"
            style={{ background: "rgba(146,43,0,0.08)" }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
              viewBox="0 0 24 24" fill="none" stroke="var(--color-brand)"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-800">
              Dossiers validés par le chef d'agence
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              Ces dossiers ont reçu le score IA et attendent votre analyse.
              Consultez le détail de chaque dossier pour rédiger votre avis motivé.
            </p>
          </div>
        </div>

        {/* Contenu */}
        {chargement ? (
          <EtatChargement message="Chargement des dossiers..." />
        ) : erreur ? (
          <EtatErreur message={erreur} />
        ) : dossiers.length === 0 ? (
          <div className="bg-white border border-gray-100 rounded-xl
                          py-16 text-center">
            <p className="text-sm text-gray-400">
              Aucun dossier en attente d'analyse.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {dossiers.map((d) => (
              <div key={d.id}
                className="bg-white border border-gray-100 rounded-xl p-5
                           hover:border-gray-200 transition-colors">
                <div className="flex items-start justify-between gap-4">

                  {/* Infos principales */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-xs font-mono text-gray-400">
                        #{String(d.id).padStart(5, "0")}
                      </span>
                      <span className="text-sm font-semibold text-gray-800">
                        {d.client_nom}
                      </span>
                      {d.necessite_comite && (
                        <span className="text-[11px] font-medium px-2 py-0.5
                                         rounded-full bg-pink-50 text-pink-600">
                          Comité requis
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-4 gap-4">
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase
                                     tracking-wide mb-0.5">
                          Type
                        </p>
                        <p className="text-sm text-gray-700">
                          {d.type_credit_display}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase
                                     tracking-wide mb-0.5">
                          Montant
                        </p>
                        <p className="text-sm text-gray-700 font-medium">
                          {formaterMontant(d.montant_sollicite)}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase
                                     tracking-wide mb-0.5">
                          Durée
                        </p>
                        <p className="text-sm text-gray-700">
                          {d.duree_mois} mois
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase
                                     tracking-wide mb-0.5">
                          Commercial
                        </p>
                        <p className="text-sm text-gray-700">
                          {d.commercial_nom}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Score IA */}
                  <div className="flex items-center gap-4 shrink-0">
                    {d.score ? (
                      <div className="text-center">
                        <div className="relative w-16 h-16">
                          {d.score !== null && (
                            <JaugeScore score={Number(d.score)} niveauRisque={String(d.niveau_risque ?? "")} taille={72} />
                          )}
                          <div className="absolute inset-0 flex flex-col
                                          items-center justify-center">
                            <span className="text-sm font-bold text-gray-800">
                              {d.score}
                            </span>
                          </div>
                        </div>
                        <span className={`text-[10px] font-medium px-2 py-0.5
                                          rounded-full mt-1 inline-block
                                          ${COULEURS_RISQUE[d.niveau_risque]}`}>
                          {d.niveau_risque}
                        </span>
                      </div>
                    ) : (
                      <div className="text-center w-16">
                        <p className="text-xs text-gray-400">Score N/A</p>
                      </div>
                    )}

                    <Link
                      href={`/dossiers/${d.id}`}
                      className="h-9 px-4 flex items-center gap-2 rounded-lg
                                 text-sm font-medium text-white transition-all
                                 hover:opacity-90"
                      style={{ background: "var(--color-brand)" }}
                    >
                      Analyser
                      <svg xmlns="http://www.w3.org/2000/svg" width="14"
                        height="14" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2"
                        strokeLinecap="round" strokeLinejoin="round">
                        <line x1="5" y1="12" x2="19" y2="12"/>
                        <polyline points="12 5 19 12 12 19"/>
                      </svg>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}