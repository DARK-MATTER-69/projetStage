"use client";

import MainLayout from "@/components/layout/MainLayout";

/** Carte de statistique */
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
        <div className="p-2 rounded-lg bg-[#922b00]/8 text-[#922b00]">
          {icon}
        </div>
      </div>
    </div>
  );
}

/** Ligne de dossier récent */
function LigneDossier({
  id,
  client,
  montant,
  statut,
  date,
}: {
  id:      number;
  client:  string;
  montant: string;
  statut:  string;
  date:    string;
}) {
  const couleurStatut: Record<string, string> = {
    "Brouillon":        "bg-gray-100 text-gray-500",
    "Soumis":           "bg-blue-50 text-blue-600",
    "Validé":           "bg-green-50 text-green-600",
    "En analyse":       "bg-orange-50 text-orange-600",
    "Approuvé":         "bg-emerald-50 text-emerald-600",
    "Rejeté":           "bg-red-50 text-red-600",
  };

  return (
    <tr className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
      <td className="py-3 px-4 text-xs font-mono text-gray-400">
        #{String(id).padStart(5, "0")}
      </td>
      <td className="py-3 px-4 text-sm text-gray-700">{client}</td>
      <td className="py-3 px-4 text-sm text-gray-700">{montant}</td>
      <td className="py-3 px-4">
        <span className={`text-[11px] font-medium px-2 py-1 rounded-full ${couleurStatut[statut] || "bg-gray-100 text-gray-500"}`}>
          {statut}
        </span>
      </td>
      <td className="py-3 px-4 text-xs text-gray-400">{date}</td>
    </tr>
  );
}

// Données de démonstration
const STATS = [
  {
    titre:       "Dossiers en cours",
    valeur:      12,
    description: "4 en attente de validation",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
    ),
  },
  {
    titre:       "Dossiers approuvés",
    valeur:      38,
    description: "Ce mois-ci",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    ),
  },
  {
    titre:       "Montant total",
    valeur:      "42,5M",
    description: "FCFA accordés ce mois",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23"/>
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
    ),
  },
  {
    titre:       "Dossiers rejetés",
    valeur:      5,
    description: "Taux de rejet : 11%",
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
    ),
  },
];

const DOSSIERS_RECENTS = [
  { id: 1, client: "Mbarga Jean-Pierre",   montant: "850 000 FCFA",   statut: "En analyse",  date: "08/08/2025" },
  { id: 2, client: "Ngo Nathalie",         montant: "1 200 000 FCFA", statut: "Soumis",      date: "07/08/2025" },
  { id: 3, client: "Fono Paul",            montant: "500 000 FCFA",   statut: "Approuvé",    date: "06/08/2025" },
  { id: 4, client: "Kameni Christelle",    montant: "2 000 000 FCFA", statut: "Validé",      date: "05/08/2025" },
  { id: 5, client: "Djomo Emmanuel",       montant: "750 000 FCFA",   statut: "Rejeté",      date: "04/08/2025" },
];

export default function DashboardPage() {
  return (
    <MainLayout titre="Tableau de bord">
      <div className="space-y-6">

        {/* Cartes statistiques */}
        <div className="grid grid-cols-4 gap-4">
          {STATS.map((s) => (
            <CarteStats key={s.titre} {...s} />
          ))}
        </div>

        {/* Dossiers récents */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-800">
              Dossiers récents
            </h2>
            <a
              href="/dossiers"
              className="text-xs hover:underline transition-colors"
              style={{ color: "#922b00" }}
            >
              Voir tout
            </a>
          </div>

          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-50">
                {["Réf.", "Client", "Montant", "Statut", "Date"].map((h) => (
                  <th
                    key={h}
                    className="py-3 px-4 text-left text-[11px] font-medium
                               text-gray-400 uppercase tracking-widest"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DOSSIERS_RECENTS.map((d) => (
                <LigneDossier key={d.id} {...d} />
              ))}
            </tbody>
          </table>
        </div>

        {/* Score IA - résumé */}
        <div className="grid grid-cols-3 gap-4">

          <div className="col-span-2 bg-white border border-gray-100 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-4">
              Répartition des scores IA
            </h2>
            <div className="space-y-3">
              {[
                { label: "Risque faible",    pct: 55, color: "#16a34a" },
                { label: "Risque moyen",     pct: 28, color: "#ea580c" },
                { label: "Risque élevé",     pct: 12, color: "#dc2626" },
                { label: "Risque critique",  pct: 5,  color: "#7f1d1d" },
              ].map(({ label, pct, color }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
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
              ))}
            </div>
          </div>

          <div className="bg-white border border-gray-100 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-4">
              Activité récente
            </h2>
            <div className="space-y-3">
              {[
                { action: "Dossier #00001 soumis",        heure: "Il y a 10 min" },
                { action: "Score IA calculé — 78/100",    heure: "Il y a 25 min" },
                { action: "Validation chef d'agence",     heure: "Il y a 1h" },
                { action: "Dossier #00003 approuvé",      heure: "Il y a 2h" },
                { action: "Nouveau client enregistré",    heure: "Il y a 3h" },
              ].map(({ action, heure }) => (
                <div key={action} className="flex items-start gap-2.5">
                  <span
                    className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0"
                    style={{ background: "#922b00" }}
                  />
                  <div>
                    <p className="text-xs text-gray-700">{action}</p>
                    <p className="text-[10px] text-gray-400">{heure}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </MainLayout>
  );
}