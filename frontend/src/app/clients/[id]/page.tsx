"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { clientsService } from "@/services/clientsService";
import { EtatChargement, EtatErreur } from "@/components/ui/EtatChargement";

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

function Info({ label, valeur }: { label: string; valeur: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="text-sm text-gray-700">{valeur || "—"}</p>
    </div>
  );
}

export default function DetailClientPage() {
  const params  = useParams();
  const router  = useRouter();
  const id      = Number(params.id);

  const [client,     setClient]     = useState<any>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur,     setErreur]     = useState("");

  useEffect(() => {
    const charger = async () => {
      try {
        const data = await clientsService.detail(id);
        setClient(data);
      } catch {
        setErreur("Client introuvable.");
      } finally {
        setChargement(false);
      }
    };
    if (id) charger();
  }, [id]);

  if (chargement) return <MainLayout titre="Client"><EtatChargement /></MainLayout>;
  if (erreur)     return <MainLayout titre="Client"><EtatErreur message={erreur} /></MainLayout>;
  if (!client)    return null;

  return (
    <MainLayout titre={`${client.civilite}. ${client.nom} ${client.prenom}`}>
      <div className="max-w-3xl mx-auto space-y-4">

        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-gray-500
                     hover:text-gray-800 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15"
            viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Retour
        </button>

        {/* Identité */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-50">
            <h2 className="text-xs font-semibold text-gray-500
                           uppercase tracking-widest">
              Identité
            </h2>
          </div>
          <div className="p-5 grid grid-cols-3 gap-4">
            <Info label="Civilité"        valeur={client.civilite_display}   />
            <Info label="Nom"             valeur={client.nom}                />
            <Info label="Prénom"          valeur={client.prenom}             />
            <Info label="Date naissance"
              valeur={new Date(client.date_naissance).toLocaleDateString("fr-FR")} />
            <Info label="Lieu naissance"  valeur={client.lieu_naissance}     />
            <Info label="Nationalité"     valeur={client.nationalite}        />
            <Info label="CNI"             valeur={client.numero_cni}         />
            <Info label="Téléphone"       valeur={client.telephone}          />
            <Info label="Email"           valeur={client.email || "—"}       />
            <Info label="Adresse"         valeur={client.adresse}            />
            {client.matricule && (
              <Info label="Matricule"     valeur={client.matricule}          />
            )}
          </div>
        </div>

        {/* Situation professionnelle */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-50">
            <h2 className="text-xs font-semibold text-gray-500
                           uppercase tracking-widest">
              Situation professionnelle
            </h2>
          </div>
          <div className="p-5 grid grid-cols-3 gap-4">
            <Info label="Type employeur"  valeur={client.type_employeur_display} />
            <Info label="Employeur"       valeur={client.nom_employeur}          />
            <Info label="Poste"           valeur={client.poste_occupe}           />
            <Info label="Ancienneté"      valeur={`${client.anciennete} ans`}    />
            <Info label="Salaire net"     valeur={formaterMontant(client.salaire_net)} />
            <Info label="Charges"         valeur={formaterMontant(client.charges_mensuelles)} />
            <Info label="Crédits en cours" valeur={formaterMontant(client.credits_en_cours)} />
            <Info label="Jour de salaire" valeur={client.date_versement_salaire || "—"} />
          </div>
        </div>

        {/* Dossiers du client */}
        {client.dossiers && client.dossiers.length > 0 && (
          <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
            <div className="px-5 py-3.5 border-b border-gray-50">
              <h2 className="text-xs font-semibold text-gray-500
                             uppercase tracking-widest">
                Dossiers associés
              </h2>
            </div>
            <div className="divide-y divide-gray-50">
              {client.dossiers.map((d: any) => (
                <div key={d.id}
                  className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      #{String(d.id).padStart(5, "0")} — {d.type_credit_display}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formaterMontant(d.montant_sollicite)} · {d.duree_mois} mois
                    </p>
                  </div>
                  <Link
                    href={`/dossiers/${d.id}`}
                    className="text-xs hover:underline"
                    style={{ color: "#922b00" }}
                  >
                    Voir →
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </MainLayout>
  );
}