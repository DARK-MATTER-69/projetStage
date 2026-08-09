"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import api from "@/lib/axios";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router         = useRouter();
  const { connexion }  = useAuthStore();

  const [username,         setUsername]         = useState("");
  const [password,         setPassword]         = useState("");
  const [afficherPassword, setAfficherPassword] = useState(false);
  const [erreur,           setErreur]           = useState("");
  const [chargement,       setChargement]       = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErreur("");
    setChargement(true);

    try {
      const { data: tokens } = await api.post("/api/auth/login/", {
        username,
        password,
      });

      const { data: utilisateur } = await api.get("/api/auth/profil/", {
        headers: { Authorization: `Bearer ${tokens.access}` },
      });

      connexion(tokens.access, tokens.refresh, utilisateur);
      router.push("/dashboard");

    } catch {
      setErreur("Identifiants incorrects. Veuillez réessayer.");
    } finally {
      setChargement(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm w-full max-w-md overflow-hidden">

        {/* En-tête */}
        <div className="bg-white border-b border-gray-100 px-8 py-7">
          <div className="flex items-center gap-4">

            {/* Logo */}
            <div className="w-14 h-14 flex-shrink-0 flex items-center justify-center">
              <Image
                src="/logo-sce.png"
                alt="Logo SCE"
                width={56}
                height={56}
                priority
                className="object-contain"
              />
            </div>

            {/* Nom entreprise */}
            <div>
              <h1 className="font-serif text-[17px] font-medium leading-snug tracking-wide"
                  style={{ color: "#922b00" }}>
                Société Camerounaise<br />d&apos;Équipements
              </h1>
              <p className="text-[11px] text-gray-400 uppercase tracking-widest mt-1">
                Gestion des dossiers de crédit
              </p>
            </div>

          </div>
        </div>

        {/* Formulaire */}
        <div className="px-8 py-7">
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Identifiant */}
            <div>
              <label
                htmlFor="username"
                className="block text-[12px] font-medium uppercase tracking-wide text-gray-500 mb-1.5"
              >
                Identifiant
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
                  </svg>
                </span>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Entrez votre identifiant"
                  required
                  autoComplete="username"
                  disabled={chargement}
                  className="w-full h-[42px] border border-gray-300 rounded-md
                             pl-[42px] pr-4 text-sm text-gray-800
                             placeholder:text-gray-400
                             focus:outline-none focus:border-[#922b00]
                             focus:ring-2 focus:ring-[#922b00]/10
                             disabled:bg-gray-50 transition-colors"
                />
              </div>
            </div>

            {/* Mot de passe */}
            <div>
              <label
                htmlFor="password"
                className="block text-[12px] font-medium uppercase tracking-wide text-gray-500 mb-1.5"
              >
                Mot de passe
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </span>
                <input
                  id="password"
                  type={afficherPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Entrez votre mot de passe"
                  required
                  autoComplete="current-password"
                  disabled={chargement}
                  className="w-full h-[42px] border border-gray-300 rounded-md
                             pl-[42px] pr-10 text-sm text-gray-800
                             placeholder:text-gray-400
                             focus:outline-none focus:border-[#922b00]
                             focus:ring-2 focus:ring-[#922b00]/10
                             disabled:bg-gray-50 transition-colors"
                />
                {/* Bouton afficher/masquer mot de passe */}
                <button
                  type="button"
                  onClick={() => setAfficherPassword(!afficherPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2
                             text-gray-400 hover:text-[#922b00]
                             transition-colors bg-transparent border-none outline-none"
                  aria-label={afficherPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                >
                  {afficherPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                      fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                      <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                      fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Erreur */}
            {erreur && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                {erreur}
              </p>
            )}

            {/* Bouton connexion */}
            <button
              type="submit"
              disabled={chargement}
              className="w-full h-[42px] border border-[#922b00] text-[#922b00]
                         bg-white rounded-md text-sm font-medium
                         hover:bg-[#922b00] hover:text-white
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-all flex items-center justify-center gap-2"
              style={{ marginTop: "1.25rem" }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                <polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>
              </svg>
              {chargement ? "Connexion en cours..." : "Se connecter"}
            </button>

          </form>

          {/* Mot de passe oublié */}
          <p className="text-center text-xs text-gray-400 hover:text-[#922b00]
                        cursor-pointer transition-colors mt-4">
            Mot de passe oublié ?
          </p>

          <hr className="border-gray-100 my-5" />

          {/* Footer */}
          <p className="text-center text-[11px] text-gray-400 flex items-center justify-center gap-1.5">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Accès réservé au personnel autorisé de la SCE
          </p>

        </div>
      </div>
    </main>
  );
}