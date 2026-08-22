"use client";

import { useState } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { useAuthStore } from "@/store/authStore";
import { LABELS_ROLES } from "@/lib/roles";
import { authService } from "@/services/authService";

interface ChampInfoProps {
  label:  string;
  valeur: string;
}

function ChampInfo({ label, valeur }: ChampInfoProps) {
  return (
    <div className="flex flex-col gap-1">
      <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="text-sm text-gray-700">{valeur || "—"}</p>
    </div>
  );
}

export default function ProfilPage() {
  const { utilisateur } = useAuthStore();

  const [nom,       setNom]       = useState(utilisateur?.last_name  || "");
  const [prenom,    setPrenom]    = useState(utilisateur?.first_name || "");
  const [email,     setEmail]     = useState(utilisateur?.email      || "");
  const [telephone, setTelephone] = useState(utilisateur?.telephone  || "");
  const [succes,    setSucces]    = useState(false);
  const [chargement, setChargement] = useState(false);

  const handleSauvegarder = async () => {
    setChargement(true);
    setSucces(false);
    await authService.modifierProfil({
      first_name: prenom,
      last_name:  nom,
      email,
      telephone,
    });
    setSucces(true);
    setChargement(false);
  };

  const inputClass = `w-full h-10 border border-gray-200 rounded-lg px-3
                      text-sm text-gray-700 placeholder:text-gray-400 bg-white
                      focus:outline-none focus:border-[var(--color-brand)]
                      focus:ring-2 focus:ring-[var(--color-brand)]/10`;

  return (
    <MainLayout titre="Mon profil">
      <div className="max-w-2xl mx-auto space-y-5">

        {/* Carte identité */}
        <div className="bg-white border border-gray-100 rounded-xl p-6">
          <div className="flex items-center gap-5">

            {/* Avatar */}
            <div className="w-16 h-16 rounded-full flex items-center justify-center
                            text-2xl font-bold shrink-0"
              style={{ background: "rgba(146,43,0,0.1)", color: "var(--color-brand)" }}>
              {utilisateur?.first_name?.[0]?.toUpperCase() || "U"}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-lg font-semibold text-gray-800">
                {utilisateur?.first_name} {utilisateur?.last_name}
              </p>
              <p className="text-sm text-gray-400 mt-0.5">
                {utilisateur?.username}
              </p>
              <span
                className="inline-block mt-2 text-[11px] font-medium px-2.5 py-1
                           rounded-full"
                style={{
                  background: "rgba(146,43,0,0.08)",
                  color:      "var(--color-brand)",
                }}
              >
                {LABELS_ROLES[utilisateur?.role || ""] || utilisateur?.role}
              </span>
            </div>

            <div className="text-right shrink-0">
              <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">
                Agence
              </p>
              <p className="text-sm font-medium text-gray-700">
                {utilisateur?.agence || "—"}
              </p>
            </div>

          </div>
        </div>

        {/* Informations non modifiables */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-50">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Informations du compte
            </h2>
          </div>
          <div className="p-5 grid grid-cols-2 gap-5">
            <ChampInfo label="Identifiant"  valeur={utilisateur?.username || ""} />
            <ChampInfo label="Rôle"         valeur={LABELS_ROLES[utilisateur?.role || ""] || ""} />
            <ChampInfo label="Agence"       valeur={utilisateur?.agence    || ""} />
          </div>
        </div>

        {/* Informations modifiables */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-50">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Modifier mes informations
            </h2>
          </div>
          <div className="p-5 space-y-4">

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500
                                   uppercase tracking-wide mb-1.5">
                  Nom
                </label>
                <input
                  type="text"
                  value={nom}
                  onChange={(e) => setNom(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500
                                   uppercase tracking-wide mb-1.5">
                  Prénom
                </label>
                <input
                  type="text"
                  value={prenom}
                  onChange={(e) => setPrenom(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500
                                 uppercase tracking-wide mb-1.5">
                Téléphone
              </label>
              <input
                type="tel"
                value={telephone}
                onChange={(e) => setTelephone(e.target.value)}
                placeholder="6XXXXXXXX"
                className={inputClass}
              />
            </div>

            {succes && (
              <p className="text-sm text-green-600 bg-green-50 border
                            border-green-100 rounded-lg px-3 py-2">
                Informations mises à jour avec succès.
              </p>
            )}

            <div className="flex items-center justify-between pt-2">
              <Link
                href="/profil/changer-mot-de-passe"
                className="text-xs hover:underline transition-colors"
                style={{ color: "var(--color-brand)" }}
              >
                Changer mon mot de passe →
              </Link>

              <button
                onClick={handleSauvegarder}
                disabled={chargement}
                className="h-10 px-5 rounded-lg text-sm font-medium
                           text-white disabled:opacity-50 transition-all"
                style={{ background: "var(--color-brand)" }}
              >
                {chargement ? "Enregistrement..." : "Sauvegarder"}
              </button>
            </div>

          </div>
        </div>

      </div>
    </MainLayout>
  );
}