"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { clientsService } from "@/services/clientsService";
import { EtatChargement, EtatErreur } from "@/components/ui/EtatChargement";

interface Client {
  id:                    number;
  civilite:              string;
  nom:                   string;
  prenom:                string;
  numero_cni:            string;
  telephone:             string;
  type_employeur_display: string;
  nom_employeur:         string;
  salaire_net:           number;
  cree_le:               string;
}

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

export default function ClientsPage() {
  const [clients,    setClients]    = useState<Client[]>([]);
  const [chargement, setChargement] = useState(true);
  const [erreur,     setErreur]     = useState("");
  const [recherche,  setRecherche]  = useState("");

  useEffect(() => {
    const charger = async () => {
      try {
        const data = await clientsService.lister();
        setClients(data.results || data);
      } catch {
        setErreur("Impossible de charger les clients.");
      } finally {
        setChargement(false);
      }
    };
    charger();
  }, []);

  const clientsFiltres = clients.filter((c) =>
    `${c.nom} ${c.prenom} ${c.numero_cni} ${c.telephone}`
      .toLowerCase()
      .includes(recherche.toLowerCase())
  );

  return (
    <MainLayout titre="Clients">
      <div className="space-y-5">

        {/* Barre de recherche */}
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
              placeholder="Rechercher par nom, CNI, téléphone..."
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              className="w-full h-9 border border-gray-200 rounded-lg
                         pl-9 pr-4 text-sm text-gray-700
                         placeholder:text-gray-400
                         focus:outline-none focus:border-[#922b00]
                         focus:ring-2 focus:ring-[#922b00]/10"
            />
          </div>

          <Link
            href="/dossiers/nouveau"
            className="h-9 px-4 flex items-center gap-2 rounded-lg text-sm
                       font-medium border border-[#922b00] text-[#922b00]
                       hover:bg-[#922b00] hover:text-white transition-all"
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

        {/* Contenu */}
        {chargement ? (
          <EtatChargement message="Chargement des clients..." />
        ) : erreur ? (
          <EtatErreur message={erreur} />
        ) : (
          <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-50">
                  {["Client", "CNI", "Téléphone", "Employeur", "Salaire net", "Date", ""].map((h) => (
                    <th key={h}
                      className="py-3 px-4 text-left text-[11px] font-medium
                                 text-gray-400 uppercase tracking-widest">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {clientsFiltres.length === 0 ? (
                  <tr>
                    <td colSpan={7}
                      className="py-12 text-center text-sm text-gray-400">
                      Aucun client trouvé
                    </td>
                  </tr>
                ) : (
                  clientsFiltres.map((c) => (
                    <tr key={c.id}
                      className="border-b border-gray-50
                                 hover:bg-gray-50/50 transition-colors">
                      <td className="py-3 px-4">
                        <p className="text-sm font-medium text-gray-800">
                          {c.civilite}. {c.nom} {c.prenom}
                        </p>
                      </td>
                      <td className="py-3 px-4 text-sm font-mono text-gray-500">
                        {c.numero_cni}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {c.telephone}
                      </td>
                      <td className="py-3 px-4">
                        <p className="text-sm text-gray-700">{c.nom_employeur}</p>
                        <p className="text-[11px] text-gray-400">
                          {c.type_employeur_display}
                        </p>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700 whitespace-nowrap">
                        {formaterMontant(c.salaire_net)}
                      </td>
                      <td className="py-3 px-4 text-xs text-gray-400">
                        {new Date(c.cree_le).toLocaleDateString("fr-FR")}
                      </td>
                      <td className="py-3 px-4">
                        <Link
                          href={`/clients/${c.id}`}
                          className="text-xs hover:underline transition-colors"
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

            <div className="px-4 py-3 border-t border-gray-50">
              <p className="text-xs text-gray-400">
                {clientsFiltres.length} client{clientsFiltres.length > 1 ? "s" : ""}
              </p>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}