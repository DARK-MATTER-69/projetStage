"use client";

import { useState } from "react";
import { useEffect } from "react";
import { adminService } from "@/services/adminService";
import { EtatChargement } from "@/components/ui/EtatChargement";
import MainLayout from "@/components/layout/MainLayout";
import { LABELS_ROLES } from "@/lib/roles";

interface Utilisateur {
  id:         number;
  username:   string;
  first_name: string;
  last_name:  string;
  email:      string;
  role:       string;
  agence:     string;
  telephone:  string;
  is_active:  boolean;
}

// Données de démonstration
const UTILISATEURS: Utilisateur[] = [
  { id: 1, username: "admin",       first_name: "Super",      last_name: "Admin",    email: "admin@sce.cm",      role: "ADMINISTRATEUR", agence: "Siège",         telephone: "677000001", is_active: true  },
  { id: 2, username: "brayann",     first_name: "Brayann",    last_name: "Noubissie", email: "brayann@sce.cm",   role: "COMMERCIAL",     agence: "Yaoundé Centre", telephone: "677000002", is_active: true  },
  { id: 3, username: "chef.yde",    first_name: "Paul",       last_name: "Ateba",    email: "pateba@sce.cm",     role: "CHEF_AGENCE",    agence: "Yaoundé Centre", telephone: "677000003", is_active: true  },
  { id: 4, username: "analyste1",   first_name: "Marie",      last_name: "Ngo",      email: "mngo@sce.cm",       role: "ANALYSTE",       agence: "Yaoundé Centre", telephone: "677000004", is_active: true  },
  { id: 5, username: "analyste2",   first_name: "Jean",       last_name: "Fono",     email: "jfono@sce.cm",      role: "ANALYSTE",       agence: "Douala",         telephone: "677000005", is_active: true  },
  { id: 6, username: "direction",   first_name: "Robert",     last_name: "Nguele",   email: "rnguele@sce.cm",    role: "DIRECTION",      agence: "Siège",          telephone: "677000006", is_active: true  },
  { id: 7, username: "comite1",     first_name: "Christelle", last_name: "Kameni",   email: "ckameni@sce.cm",    role: "COMITE",         agence: "Siège",          telephone: "677000007", is_active: true  },
  { id: 8, username: "comm.dla",    first_name: "Cécile",     last_name: "Essomba",  email: "cessomba@sce.cm",   role: "COMMERCIAL",     agence: "Douala",         telephone: "677000008", is_active: false },
];

const COULEURS_ROLES: Record<string, string> = {
  ADMINISTRATEUR: "bg-purple-50 text-purple-600",
  COMMERCIAL:     "bg-blue-50 text-blue-600",
  CHEF_AGENCE:    "bg-indigo-50 text-indigo-600",
  ANALYSTE:       "bg-orange-50 text-orange-600",
  DIRECTION:      "bg-green-50 text-green-600",
  COMITE:         "bg-pink-50 text-pink-600",
};

interface ModalUtilisateurProps {
  utilisateur: Utilisateur | null;
  onFermer:    () => void;
  onSauvegarder: (u: Utilisateur) => void;
}

function ModalUtilisateur({ utilisateur, onFermer, onSauvegarder }: ModalUtilisateurProps) {
  const estNouveau = utilisateur === null;

  const [form, setForm] = useState<Omit<Utilisateur, "id">>({
    username:   utilisateur?.username   || "",
    first_name: utilisateur?.first_name || "",
    last_name:  utilisateur?.last_name  || "",
    email:      utilisateur?.email      || "",
    role:       utilisateur?.role       || "COMMERCIAL",
    agence:     utilisateur?.agence     || "",
    telephone:  utilisateur?.telephone  || "",
    is_active:  utilisateur?.is_active  ?? true,
  });

  const [password,    setPassword]    = useState("");
  const [chargement,  setChargement]  = useState(false);

  const maj = (champ: keyof typeof form, val: string | boolean) =>
    setForm((prev) => ({ ...prev, [champ]: val }));

  const handleSubmit = async () => {
    setChargement(true);
    await new Promise((r) => setTimeout(r, 800));
    onSauvegarder({
      id: utilisateur?.id || Date.now(),
      ...form,
    });
    setChargement(false);
  };

  const inputClass = `w-full h-10 border border-gray-200 rounded-lg px-3
                      text-sm text-gray-700 bg-white
                      focus:outline-none focus:border-[var(--color-brand)]
                      focus:ring-2 focus:ring-[var(--color-brand)]/10`;

  const selectClass = `w-full h-10 border border-gray-200 rounded-lg px-3
                       text-sm text-gray-700 bg-white
                       focus:outline-none focus:border-[var(--color-brand)]
                       focus:ring-2 focus:ring-[var(--color-brand)]/10`;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center
                    justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg">

        {/* En-tête */}
        <div className="flex items-center justify-between px-5 py-4
                        border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-800">
            {estNouveau ? "Créer un utilisateur" : "Modifier l'utilisateur"}
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
          <div className="grid grid-cols-2 gap-4">

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Prénom
              </label>
              <input type="text" value={form.first_name}
                onChange={(e) => maj("first_name", e.target.value)}
                className={inputClass} />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Nom
              </label>
              <input type="text" value={form.last_name}
                onChange={(e) => maj("last_name", e.target.value)}
                className={inputClass} />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Identifiant
              </label>
              <input type="text" value={form.username}
                onChange={(e) => maj("username", e.target.value)}
                disabled={!estNouveau}
                className={inputClass + " disabled:bg-gray-50 disabled:text-gray-400"} />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Email
              </label>
              <input type="email" value={form.email}
                onChange={(e) => maj("email", e.target.value)}
                className={inputClass} />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Téléphone
              </label>
              <input type="tel" value={form.telephone}
                onChange={(e) => maj("telephone", e.target.value)}
                placeholder="6XXXXXXXX"
                className={inputClass} />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Agence
              </label>
              <input type="text" value={form.agence}
                onChange={(e) => maj("agence", e.target.value)}
                placeholder="Yaoundé Centre"
                className={inputClass} />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Rôle
              </label>
              <select value={form.role}
                onChange={(e) => maj("role", e.target.value)}
                className={selectClass}>
                {Object.entries(LABELS_ROLES).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            {estNouveau && (
              <div>
                <label className="block text-xs font-medium text-gray-500
                                   uppercase tracking-wide mb-1.5">
                  Mot de passe
                </label>
                <input type="password" value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 8 caractères"
                  className={inputClass} />
              </div>
            )}

          </div>

          {/* Compte actif */}
          <div className="flex items-center gap-3 pt-1">
            <button
              type="button"
              onClick={() => maj("is_active", !form.is_active)}
              className={`w-10 h-5 rounded-full transition-colors relative
                          ${form.is_active ? "bg-[var(--color-brand)]" : "bg-gray-200"}`}
            >
              <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full
                                shadow transition-transform
                                ${form.is_active ? "translate-x-5" : "translate-x-0.5"}`} />
            </button>
            <span className="text-sm text-gray-600">
              Compte {form.is_active ? "actif" : "désactivé"}
            </span>
          </div>

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
              disabled={chargement}
              className="flex-1 h-10 rounded-lg text-sm font-medium
                         text-white disabled:opacity-50 transition-all"
              style={{ background: "var(--color-brand)" }}
            >
              {chargement ? "Enregistrement..." : "Sauvegarder"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminUtilisateursPage() {
  const [utilisateurs,     setUtilisateurs]     = useState<Utilisateur[]>([]);
const [chargement,       setChargement]       = useState(true);
const [modalOuverte,     setModalOuverte]     = useState(false);
const [utilisateurEdite, setUtilisateurEdite] = useState<Utilisateur | null>(null);
const [recherche,        setRecherche]        = useState("");

useEffect(() => {
  const charger = async () => {
    try {
      const data = await adminService.listerUtilisateurs();
      setUtilisateurs(data.results || data);
    } catch {
      // Silencieux
    } finally {
      setChargement(false);
    }
  };
  charger();
}, []);

const handleSauvegarder = async (u: Utilisateur) => {
  try {
    if (utilisateurEdite) {
      await adminService.modifierUtilisateur(u.id, {
        first_name: u.first_name,
        last_name:  u.last_name,
        email:      u.email,
        role:       u.role,
        agence:     u.agence,
        telephone:  u.telephone,
        is_active:  u.is_active,
      });
    } else {
      await adminService.creerUtilisateur({
        username:   u.username,
        first_name: u.first_name,
        last_name:  u.last_name,
        email:      u.email,
        role:       u.role,
        agence:     u.agence,
        telephone:  u.telephone,
        password:   "Sce@2025!", // Mot de passe temporaire
      });
    }
    // Recharger la liste
    const data = await adminService.listerUtilisateurs();
    setUtilisateurs(data.results || data);
  } catch {
    // Silencieux
  }
  setModalOuverte(false);
  setUtilisateurEdite(null);
};

const handleToggleActif = async (id: number) => {
  const u = utilisateurs.find((x) => x.id === id);
  if (!u) return;
  try {
    await adminService.modifierUtilisateur(id, { is_active: !u.is_active });
    setUtilisateurs((prev) =>
      prev.map((x) => x.id === id ? { ...x, is_active: !x.is_active } : x)
    );
  } catch {
    // Silencieux
  }
};

  const utilisateursFiltres = utilisateurs.filter((u) =>
    `${u.first_name} ${u.last_name} ${u.username} ${u.email}`
      .toLowerCase()
      .includes(recherche.toLowerCase())
  );
  
  return (
    <MainLayout titre="Gestion des utilisateurs">
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
              placeholder="Rechercher un utilisateur..."
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              className="w-full h-9 border border-gray-200 rounded-lg
                         pl-9 pr-4 text-sm text-gray-700
                         placeholder:text-gray-400
                         focus:outline-none focus:border-[var(--color-brand)]
                         focus:ring-2 focus:ring-[var(--color-brand)]/10"
            />
          </div>

          <button
            onClick={() => { setUtilisateurEdite(null); setModalOuverte(true); }}
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
            Nouvel utilisateur
          </button>
        </div>

        {/* Tableau */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-50">
                {["Utilisateur", "Identifiant", "Rôle", "Agence", "Statut", ""].map((h) => (
                  <th key={h}
                    className="py-3 px-4 text-left text-[11px] font-medium
                               text-gray-400 uppercase tracking-widest">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {utilisateursFiltres.map((u) => (
                <tr key={u.id}
                  className="border-b border-gray-50 hover:bg-gray-50/50
                             transition-colors">

                  {/* Utilisateur */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full flex items-center
                                      justify-center text-sm font-semibold
                                      flex-shrink-0"
                        style={{
                          background: "rgba(146,43,0,0.08)",
                          color:      "var(--color-brand)",
                        }}>
                        {u.first_name[0]}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {u.first_name} {u.last_name}
                        </p>
                        <p className="text-[11px] text-gray-400">{u.email}</p>
                      </div>
                    </div>
                  </td>

                  {/* Identifiant */}
                  <td className="py-3 px-4 text-sm font-mono text-gray-500">
                    {u.username}
                  </td>

                  {/* Rôle */}
                  <td className="py-3 px-4">
                    <span className={`text-[11px] font-medium px-2 py-1
                                      rounded-full ${COULEURS_ROLES[u.role]}`}>
                      {LABELS_ROLES[u.role]}
                    </span>
                  </td>

                  {/* Agence */}
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {u.agence}
                  </td>

                  {/* Statut */}
                  <td className="py-3 px-4">
                    <button
                      onClick={() => handleToggleActif(u.id)}
                      className={`w-9 h-5 rounded-full transition-colors relative`}
                      style={{ background: u.is_active ? "var(--color-brand)" : "#e5e7eb" }}
                    >
                      <span className={`absolute top-0.5 w-4 h-4 bg-white
                                        rounded-full shadow transition-transform
                                        ${u.is_active
                                          ? "translate-x-4"
                                          : "translate-x-0.5"}`} />
                    </button>
                  </td>

                  {/* Actions */}
                  <td className="py-3 px-4">
                    <button
                      onClick={() => {
                        setUtilisateurEdite(u);
                        setModalOuverte(true);
                      }}
                      className="text-xs hover:underline transition-colors"
                      style={{ color: "var(--color-brand)" }}
                    >
                      Modifier
                    </button>
                  </td>

                </tr>
              ))}
            </tbody>
          </table>

          <div className="px-4 py-3 border-t border-gray-50">
            <p className="text-xs text-gray-400">
              {utilisateursFiltres.length} utilisateur{utilisateursFiltres.length > 1 ? "s" : ""}
            </p>
          </div>
        </div>
      </div>

      {/* Modal */}
      {modalOuverte && (
        <ModalUtilisateur
          utilisateur={utilisateurEdite}
          onFermer={() => {
            setModalOuverte(false);
            setUtilisateurEdite(null);
          }}
          onSauvegarder={handleSauvegarder}
        />
      )}
    </MainLayout>
  );
}