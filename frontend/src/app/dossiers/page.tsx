"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { dossiersService } from "@/services/dossiersService";
import { EtatChargement, EtatErreur } from "@/components/ui/EtatChargement";

type Statut =
  | "BROUILLON"
  | "PRET_A_SOUMETTRE"
  | "SOUMIS"
  | "VALIDE_CHEF_COMMERCIAL"
  | "EN_ANALYSE_1"
  | "EN_ANALYSE_2"
  | "ANALYSE_TERMINEE"
  | "VALIDE_CHEF_ANALYSTE"
  | "EN_DECISION"
  | "EN_COMITE"
  | "APPROUVE"
  | "REJETE";;

interface Dossier {
  id:                number;
  client_nom:        string;
  commercial_nom:    string;
  type_credit:       string;
  type_credit_display: string;
  montant_sollicite: number;
  duree_mois:        number;
  statut:            Statut;
  statut_display:    string;
  necessite_comite:  boolean;
  cree_le:           string;
}

const STATUTS: Record<Statut, string> = {
  BROUILLON:         "bg-gray-100 text-gray-500",
  PRET_A_SOUMETTRE:  "bg-gray-100 text-gray-600",
  SOUMIS:            "bg-blue-50 text-blue-600",
  VALIDE_CHEF_COMMERCIAL:     "bg-indigo-50 text-indigo-600",
  EN_ANALYSE_1:      "bg-orange-50 text-orange-600",
  EN_ANALYSE_2:      "bg-orange-50 text-orange-700",
  ANALYSE_TERMINEE:  "bg-yellow-50 text-yellow-700",
  VALIDE_CHEF_ANALYSTE:     "bg-indigo-50 text-indigo-700",
  EN_DECISION:       "bg-purple-50 text-purple-600",
  EN_COMITE:         "bg-pink-50 text-pink-600",
  APPROUVE:          "bg-green-50 text-green-600",
  REJETE:            "bg-red-50 text-red-600",
};;

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

export default function DossiersPage() {
  const [dossiers,     setDossiers]     = useState<Dossier[]>([]);
  const [chargement,   setChargement]   = useState(true);
  const [erreur,       setErreur]       = useState("");
  const [recherche,    setRecherche]    = useState("");
  const [filtreStatut, setFiltreStatut] = useState("TOUS");

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

  const dossiersFiltres = dossiers.filter((d) => {
    const matchRecherche =
      d.client_nom.toLowerCase().includes(recherche.toLowerCase()) ||
      String(d.id).includes(recherche);
    const matchStatut =
      filtreStatut === "TOUS" || d.statut === filtreStatut;
    return matchRecherche && matchStatut;
  });

  return (
    <MainLayout titre="Dossiers de crédit">
      <div className="space-y-5">

        {/* Barre d'actions */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <span className="absolute left-3 top-1/2 -translate-y-1/2
                             text-gray-400 pointer-events-none">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            </span>
            <input
              type="text"
              placeholder="Rechercher un client ou une référence..."
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              className="w-full h-9 border border-gray-200 rounded-lg
                         pl-9 pr-4 text-sm text-gray-700
                         placeholder:text-gray-400
                         focus:outline-none focus:border-[var(--color-brand)]
                         focus:ring-2 focus:ring-[var(--color-brand)]/10"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={filtreStatut}
              onChange={(e) => setFiltreStatut(e.target.value)}
              className="h-9 border border-gray-200 rounded-lg px-3 text-sm
                         text-gray-600 focus:outline-none focus:border-[var(--color-brand)] bg-white"
            >
              <option value="TOUS">Tous les statuts</option>
              {Object.keys(STATUTS).map((key) => (
                <option key={key} value={key}>{key}</option>
              ))}
            </select>

            <Link
              href="/dossiers/nouveau"
              className="h-9 px-4 flex items-center gap-2 rounded-lg text-sm
                         font-medium border border-[var(--color-brand)] text-[var(--color-brand)]
                         hover:bg-[var(--color-brand)] hover:text-white transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Nouveau dossier
            </Link>
          </div>
        </div>

        {/* Contenu */}
        {chargement ? (
          <EtatChargement message="Chargement des dossiers..." />
        ) : erreur ? (
          <EtatErreur message={erreur} />
        ) : (
          <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-50">
                  {["Réf.", "Client", "Type", "Montant", "Durée", "Statut", "Comité", "Date", ""].map((h) => (
                    <th key={h}
                      className="py-3 px-4 text-left text-[11px] font-medium
                                 text-gray-400 uppercase tracking-widest">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dossiersFiltres.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-sm text-gray-400">
                      Aucun dossier trouvé
                    </td>
                  </tr>
                ) : (
                  dossiersFiltres.map((d) => (
                    <tr key={d.id}
                      className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                      <td className="py-3 px-4 text-xs font-mono text-gray-400">
                        #{String(d.id).padStart(5, "0")}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700 font-medium">
                        {d.client_nom}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {d.type_credit_display}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700 whitespace-nowrap">
                        {formaterMontant(d.montant_sollicite)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {d.duree_mois} mois
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-[11px] font-medium px-2 py-1
                                          rounded-full ${STATUTS[d.statut]}`}>
                          {d.statut_display}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {d.necessite_comite ? (
                          <span className="text-[11px] font-medium px-2 py-1
                                           rounded-full bg-pink-50 text-pink-600">
                            Oui
                          </span>
                        ) : (
                          <span className="text-[11px] text-gray-300">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-400 whitespace-nowrap">
                        {new Date(d.cree_le).toLocaleDateString("fr-FR")}
                      </td>
                      <td className="py-3 px-4">
                        <Link
                          href={`/dossiers/${d.id}`}
                          className="text-xs hover:underline transition-colors"
                          style={{ color: "var(--color-brand)" }}
                        >
                          Voir →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            <div className="px-4 py-3 border-t border-gray-50">
              <p className="text-xs text-gray-400">
                {dossiersFiltres.length} dossier{dossiersFiltres.length > 1 ? "s" : ""}
              </p>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}