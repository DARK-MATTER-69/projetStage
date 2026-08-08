"use client";

import { useState, FormEvent } from "react";
import api from "@/lib/axios";

export default function ChangerMotDePassePage() {
  const [ancienMdp,   setAncienMdp]   = useState("");
  const [nouveauMdp,  setNouveauMdp]  = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message,     setMessage]     = useState<{ type: "succes" | "erreur"; texte: string } | null>(null);
  const [chargement,  setChargement]  = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (nouveauMdp !== confirmation) {
      setMessage({ type: "erreur", texte: "Les deux mots de passe ne correspondent pas." });
      return;
    }

    if (nouveauMdp.length < 8) {
      setMessage({ type: "erreur", texte: "Le mot de passe doit contenir au moins 8 caractères." });
      return;
    }

    setChargement(true);

    try {
      await api.post("/api/auth/mot-de-passe/modifier/", {
        ancien_mot_de_passe:  ancienMdp,
        nouveau_mot_de_passe: nouveauMdp,
      });

      setMessage({ type: "succes", texte: "Mot de passe modifié avec succès." });
      setAncienMdp("");
      setNouveauMdp("");
      setConfirmation("");

    } catch (err: unknown) {
      const error = err as { response?: { data?: { ancien_mot_de_passe?: string[] } } };
      if (error.response?.data?.ancien_mot_de_passe) {
        setMessage({ type: "erreur", texte: "Ancien mot de passe incorrect." });
      } else {
        setMessage({ type: "erreur", texte: "Une erreur est survenue. Veuillez réessayer." });
      }
    } finally {
      setChargement(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10">
      <h1 className="text-lg font-bold text-gray-900 mb-6">
        Changer le mot de passe
      </h1>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded p-6 space-y-4">

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ancien mot de passe
          </label>
          <input
            type="password"
            value={ancienMdp}
            onChange={(e) => setAncienMdp(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm
                       focus:outline-none focus:border-gray-500"
            disabled={chargement}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nouveau mot de passe
          </label>
          <input
            type="password"
            value={nouveauMdp}
            onChange={(e) => setNouveauMdp(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm
                       focus:outline-none focus:border-gray-500"
            disabled={chargement}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Confirmer le nouveau mot de passe
          </label>
          <input
            type="password"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            required
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm
                       focus:outline-none focus:border-gray-500"
            disabled={chargement}
          />
        </div>

        {message && (
          <p className={`text-sm rounded px-3 py-2 border ${
            message.type === "succes"
              ? "text-green-700 bg-green-50 border-green-200"
              : "text-red-600 bg-red-50 border-red-200"
          }`}>
            {message.texte}
          </p>
        )}

        <button
          type="submit"
          disabled={chargement}
          className="w-full bg-gray-900 text-white text-sm font-medium
                     py-2 rounded hover:bg-gray-700
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
        >
          {chargement ? "Modification en cours..." : "Modifier le mot de passe"}
        </button>

      </form>
    </div>
  );
}