"use client";

import { useState } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";

type Statut =
  | "BROUILLON"
  | "SOUMIS"
  | "VALIDE_CHEF"
  | "EN_ANALYSE"
  | "ANALYSE_TERMINEE"
  | "VALIDE_DIRECTION"
  | "EN_COMITE"
  | "APPROUVE"
  | "REJETE";

interface Dossier {
  id:               number;
  client_nom:       string;
  commercial_nom:   string;
  type_credit:      string;
  montant_sollicite: number;
  duree_mois:       number;
  statut:           Statut;
  necessite_comite: boolean;
  cree_le:          string;
}

const STATUTS: Record<Statut, { label: string; classe: string }> = {
  BROUILLON:         { label: "Brouillon",            classe: "bg-gray-100 text-gray-500"       },
  SOUMIS:            { label: "Soumis",               classe: "bg-blue-50 text-blue-600"        },
  VALIDE_CHEF:       { label: "Validé chef",          classe: "bg-indigo-50 text-indigo-600"    },
  EN_ANALYSE:        { label: "En analyse",           classe: "bg-orange-50 text-orange-600"    },
  ANALYSE_TERMINEE:  { label: "Analyse terminée",     classe: "bg-yellow-50 text-yellow-700"    },
  VALIDE_DIRECTION:  { label: "Validé direction",     classe: "bg-purple-50 text-purple-600"    },
  EN_COMITE:         { label: "En comité",            classe: "bg-pink-50 text-pink-600"        },
  APPROUVE:          { label: "Approuvé",             classe: "bg-green-50 text-green-600"      },
  REJETE:            { label: "Rejeté",               classe: "bg-red-50 text-red-600"          },
};

// Données de démonstration
const DOSSIERS: Dossier[] = [
  { id: 1, client_nom: "Mbarga Jean-Pierre",  commercial_nom: "Noubissie Brayann", type_credit: "Équipement",   montant_sollicite: 850000,   duree_mois: 12, statut: "EN_ANALYSE",       necessite_comite: false, cree_le: "2025-08-08" },
  { id: 2, client_nom: "Ngo Nathalie",        commercial_nom: "Noubissie Brayann", type_credit: "Consommation", montant_sollicite: 1200000,  duree_mois: 24, statut: "SOUMIS",           necessite_comite: false, cree_le: "2025-08-07" },
  { id: 3, client_nom: "Fono Paul",           commercial_nom: "Noubissie Brayann", type_credit: "Scolaire",     montant_sollicite: 500000,   duree_mois: 6,  statut: "APPROUVE",         necessite_comite: false, cree_le: "2025-08-06" },
  { id: 4, client_nom: "Kameni Christelle",   commercial_nom: "Noubissie Brayann", type_credit: "Équipement",   montant_sollicite: 2000000,  duree_mois: 36, statut: "VALIDE_CHEF",      necessite_comite: false, cree_le: "2025-08-05" },
  { id: 5, client_nom: "Djomo Emmanuel",      commercial_nom: "Noubissie Brayann", type_credit: "Consommation", montant_sollicite: 750000,   duree_mois: 18, statut: "REJETE",           necessite_comite: false, cree_le: "2025-08-04" },
  { id: 6, client_nom: "Ateba Martin",        commercial_nom: "Noubissie Brayann", type_credit: "Équipement",   montant_sollicite: 6500000,  duree_mois: 36, statut: "EN_COMITE",        necessite_comite: true,  cree_le: "2025-08-03" },
  { id: 7, client_nom: "Essomba Cécile",      commercial_nom: "Noubissie Brayann", type_credit: "Scolaire",     montant_sollicite: 300000,   duree_mois: 6,  statut: "BROUILLON",        necessite_comite: false, cree_le: "2025-08-02" },
  { id: 8, client_nom: "Nguele Robert",       commercial_nom: "Noubissie Brayann", type_credit: "Bail",         montant_sollicite: 8000000,  duree_mois: 48, statut: "ANALYSE_TERMINEE", necessite_comite: true,  cree_le: "2025-08-01" },
];

const formaterMontant = (montant: number) =>
  new Intl.NumberFormat("fr-FR").format(montant) + " FCFA";

export default function DossiersPage() {
  const [recherche,      setRecherche]      = useState("");
  const [filtreStatut,   setFiltreStatut]   = useState<string>("TOUS");
  const [filtreComite,   setFiltreComite]   = useState<string>("TOUS");

  const dossiersFiltres = DOSSIERS.filter((d) => {
    const matchRecherche =
      d.client_nom.toLowerCase().includes(recherche.toLowerCase()) ||
      String(d.id).includes(recherche);

    const matchStatut =
      filtreStatut === "TOUS" || d.statut === filtreStatut;

    const matchComite =
      filtreComite === "TOUS" ||
      (filtreComite === "OUI" && d.necessite_comite) ||
      (filtreComite === "NON" && !d.necessite_comite);

    return matchRecherche && matchStatut && matchComite;
  });

  return (
    <MainLayout titre="Dossiers de crédit">
      <div className="space-y-5">

        {/* Barre d'actions */}
        <div className="flex items-center justify-between gap-4">

          {/* Recherche */}
          <div className="relative flex-1 max-w-sm">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
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
                         focus:outline-none focus:border-[#922b00]
                         focus:ring-2 focus:ring-[#922b00]/10"
            />
          </div>

          <div className="flex items-center gap-2">
            {/* Filtre statut */}
            <select
              value={filtreStatut}
              onChange={(e) => setFiltreStatut(e.target.value)}
              className="h-9 border border-gray-200 rounded-lg px-3 text-sm
                         text-gray-600 focus:outline-none focus:border-[#922b00]
                         bg-white"
            >
              <option value="TOUS">Tous les statuts</option>
              {Object.entries(STATUTS).map(([key, { label }]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>

            {/* Filtre comité */}
            <select
              value={filtreComite}
              onChange={(e) => setFiltreComite(e.target.value)}
              className="h-9 border border-gray-200 rounded-lg px-3 text-sm
                         text-gray-600 focus:outline-none focus:border-[#922b00]
                         bg-white"
            >
              <option value="TOUS">Tous</option>
              <option value="OUI">Nécessite comité</option>
              <option value="NON">Sans comité</option>
            </select>

            {/* Nouveau dossier */}
            <Link
              href="/dossiers/nouveau"
              className="h-9 px-4 flex items-center gap-2 rounded-lg text-sm
                         font-medium border border-[#922b00] text-[#922b00]
                         hover:bg-[#922b00] hover:text-white transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Nouveau dossier
            </Link>
          </div>
        </div>

        {/* Tableau */}
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
                      {d.type_credit}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-700 whitespace-nowrap">
                      {formaterMontant(d.montant_sollicite)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {d.duree_mois} mois
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[11px] font-medium px-2 py-1 rounded-full
                                        ${STATUTS[d.statut].classe}`}>
                        {STATUTS[d.statut].label}
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
                        className="text-xs hover:underline transition-colors whitespace-nowrap"
                        style={{ color: "#922b00" }}
                      >
                        Voir →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pied de tableau */}
          <div className="px-4 py-3 border-t border-gray-50 flex items-center justify-between">
            <p className="text-xs text-gray-400">
              {dossiersFiltres.length} dossier{dossiersFiltres.length > 1 ? "s" : ""}
            </p>
          </div>
        </div>

      </div>
    </MainLayout>
  );
}