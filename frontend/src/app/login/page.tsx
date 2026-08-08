"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import api from "@/lib/axios";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router        = useRouter();
  const { connexion } = useAuthStore();

  const [username,    setUsername]    = useState("");
  const [password,    setPassword]    = useState("");
  const [erreur,      setErreur]      = useState("");
  const [chargement,  setChargement]  = useState(false);

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
    <main className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white border border-gray-200 rounded shadow-sm w-full max-w-md p-8">

        {/* En-tête */}
        <div className="text-center mb-8">

          <div className="flex justify-center mb-5">
            <Image
              src="/logo-sce.png"
              alt="Logo SCE"
              width={110}
              height={110}
              priority
            />
          </div>

          <h1 className="text-2xl font-bold italic text-orange-600 tracking-wide leading-snug">
            Société Camerounaise
          </h1>
          <h1 className="text-2xl font-bold italic text-orange-600 tracking-wide leading-snug">
            d&apos;Équipements
          </h1>

          <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">
            Plateforme de gestion des dossiers de crédit
          </p>

          <hr className="mt-4 border-orange-200" />
        </div>

        {/* Formulaire */}
        <form onSubmit={handleSubmit} className="space-y-5">

          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-orange-700 mb-1"
            >
              Identifiant
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm
                         focus:outline-none focus:border-orange-500
                         disabled:bg-gray-50"
              disabled={chargement}
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-orange-700 mb-1"
            >
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm
                         focus:outline-none focus:border-orange-500
                         disabled:bg-gray-50"
              disabled={chargement}
            />
          </div>

          {/* Message d'erreur */}
          {erreur && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {erreur}
            </p>
          )}

          <button
            type="submit"
            disabled={chargement}
            className="w-full bg-orange-600 text-white text-sm font-medium
                       py-2 rounded hover:bg-orange-700
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            {chargement ? "Connexion en cours..." : "Se connecter"}
          </button>

        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          Accès réservé au personnel autorisé de la SCE
        </p>

      </div>
    </main>
  );
}