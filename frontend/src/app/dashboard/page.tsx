"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import api from "@/lib/axios";
import { EtatChargement } from "@/components/ui/EtatChargement";

interface StatsDashboard {
  dossiers_en_cours:  number;
  dossiers_approuves: number;
  dossiers_rejetes:   number;
  montant_total:      number;
}

interface DossierRecent {
  id:                number;
  client_nom:        string;
  montant_sollicite: number;
  statut:            string;
  statut_display:    string;
  cree_le:           string;
}

interface RepartitionScore {
  niveau_risque: string;
  count:         number;
}

const COULEURS_STATUT: Record<string, string> = {
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
};

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

function CarteStats({
  titre,
  valeur,
  description,
  icon,
}: {
  titre:       string;
  valeur:      string | number;
  description: string;
  icon:        React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">
            {titre}
          </p>
          <p className="text-2xl font-semibold text-gray-800">{valeur}</p>
          <p className="text-xs text-gray-400 mt-1">{description}</p>
        </div>
        <div className="p-2 rounded-lg" style={{ background: "rgba(146,43,0,0.08)" }}>
          <span style={{ color: "var(--color-brand)" }}>{icon}</span>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats,       setStats]       = useState<StatsDashboard | null>(null);
  const [recents,     setRecents]     = useState<DossierRecent[]>([]);
  const [repartition, setRepartition] = useState<RepartitionScore[]>([]);
  const [chargement,  setChargement]  = useState(true);

  useEffect(() => {
    const charger = async () => {
      try {
        const [statsRes, dossiersRes, scoringRes] = await Promise.all([
          api.get("/api/dossiers/dashboard/stats/"),
          api.get("/api/dossiers/?page_size=5"),
          api.get("/api/scoring/repartition/"),
        ]);

        setStats(statsRes.data);
        setRecents(dossiersRes.data.results || dossiersRes.data);
        setRepartition(scoringRes.data);
      } catch {
        // Si les endpoints stats/repartition n'existent pas encore
        // on charge juste les dossiers récents
        try {
          const res = await api.get("/api/dossiers/");
          const dossiers = res.data.results || res.data;
          setRecents(dossiers.slice(0, 5));

          // Stats calculées côté frontend en attendant
          setStats({
            dossiers_en_cours:  dossiers.filter((d: DossierRecent) =>
              !["APPROUVE", "REJETE", "BROUILLON"].includes(d.statut)).length,
            dossiers_approuves: dossiers.filter((d: DossierRecent) =>
              d.statut === "APPROUVE").length,
            dossiers_rejetes:   dossiers.filter((d: DossierRecent) =>
              d.statut === "REJETE").length,
            montant_total:      0,
          });
        } catch {
          // Silencieux
        }
      } finally {
        setChargement(false);
      }
    };
    charger();
  }, []);

  if (chargement) {
    return (
      <MainLayout titre="Tableau de bord">
        <EtatChargement message="Chargement du tableau de bord..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout titre="Tableau de bord">
      <div className="space-y-6">

        {/* Cartes statistiques */}
        <div className="grid grid-cols-4 gap-4">
          <CarteStats
            titre="Dossiers en cours"
            valeur={stats?.dossiers_en_cours ?? "—"}
            description="En attente de validation"
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            }
          />
          <CarteStats
            titre="Dossiers approuvés"
            valeur={stats?.dossiers_approuves ?? "—"}
            description="Total approuvés"
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            }
          />
          <CarteStats
            titre="Montant total"
            valeur={stats?.montant_total
              ? new Intl.NumberFormat("fr-FR").format(stats.montant_total) + " FCFA"
              : "—"
            }
            description="Accordé ce mois"
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            }
          />
          <CarteStats
            titre="Dossiers rejetés"
            valeur={stats?.dossiers_rejetes ?? "—"}
            description="Total rejetés"
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            }
          />
        </div>

        <div className="grid grid-cols-3 gap-4">

          {/* Dossiers récents */}
          <div className="col-span-2 bg-white border border-gray-100
                          rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-50
                            flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-800">
                Dossiers récents
              </h2>
              <Link
                href="/dossiers"
                className="text-xs hover:underline"
                style={{ color: "var(--color-brand)" }}
              >
                Voir tout →
              </Link>
            </div>

            {recents.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-10">
                Aucun dossier pour le moment.
              </p>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-50">
                    {["Réf.", "Client", "Montant", "Statut", "Date"].map((h) => (
                      <th key={h}
                        className="py-3 px-4 text-left text-[11px] font-medium
                                   text-gray-400 uppercase tracking-widest">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recents.map((d) => (
                    <tr key={d.id}
                      className="border-b border-gray-50
                                 hover:bg-gray-50/50 transition-colors">
                      <td className="py-3 px-4 text-xs font-mono text-gray-400">
                        #{String(d.id).padStart(5, "0")}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700 font-medium">
                        {d.client_nom}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700 whitespace-nowrap">
                        {formaterMontant(d.montant_sollicite)}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-[11px] font-medium px-2 py-1
                                          rounded-full
                                          ${COULEURS_STATUT[d.statut] || "bg-gray-100 text-gray-500"}`}>
                          {d.statut_display}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-400">
                        {new Date(d.cree_le).toLocaleDateString("fr-FR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Répartition scores */}
          <div className="bg-white border border-gray-100 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-4">
              Répartition des scores IA
            </h2>

            {repartition.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-6">
                Aucune donnée disponible.
              </p>
            ) : (
              <div className="space-y-3">
                {[
                  { label: "Risque faible",   key: "FAIBLE",   color: "#16a34a" },
                  { label: "Risque moyen",    key: "MOYEN",    color: "#ea580c" },
                  { label: "Risque élevé",    key: "ELEVE",    color: "#dc2626" },
                  { label: "Risque critique", key: "CRITIQUE", color: "#7f1d1d" },
                ].map(({ label, key, color }) => {
                  const item  = repartition.find((r) => r.niveau_risque === key);
                  const total = repartition.reduce((s, r) => s + r.count, 0);
                  const pct   = item && total > 0
                    ? Math.round((item.count / total) * 100)
                    : 0;

                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs
                                      text-gray-500 mb-1">
                        <span>{label}</span>
                        <span className="font-medium">{pct}%</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{ width: `${pct}%`, background: color }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

      </div>
    </MainLayout>
  );
}