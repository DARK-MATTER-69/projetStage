"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import MainLayout from "@/components/layout/MainLayout";
import { dossiersService } from "@/services/dossiersService";
import { EtatChargement, EtatErreur } from "@/components/ui/EtatChargement";
import JaugeScore from "@/components/ui/JaugeScore";
import { useAuthStore } from "@/store/authStore";

// Garder toutes les interfaces et composants Info, Section du fichier existant
// Remplacer uniquement la fonction principale

export default function DetailDossierPage() {
  const params  = useParams();
  const router  = useRouter();
  const id      = Number(params.id);

  const [dossier,    setDossier]    = useState<any>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur,     setErreur]     = useState("");

  useEffect(() => {
    const charger = async () => {
      try {
        const data = await dossiersService.detail(id);
        setDossier(data);
      } catch {
        setErreur("Dossier introuvable.");
      } finally {
        setChargement(false);
      }
    };
    if (id) charger();
  }, [id]);

  if (chargement) return <MainLayout titre="Dossier"><EtatChargement /></MainLayout>;
  if (erreur)     return <MainLayout titre="Dossier"><EtatErreur message={erreur} /></MainLayout>;
  if (!dossier)   return null;

  const score          = dossier.score;
  const d              = dossier;
  const jaugeScore     = score ? (score.score / 100) * 100 : 0;
  const couleurJauge   =
    !score         ? "#9ca3af" :
    score.score >= 70 ? "#16a34a" :
    score.score >= 50 ? "#ea580c" : "#dc2626";

  const COULEURS_RISQUE: Record<string, string> = {
    FAIBLE:   "text-green-600 bg-green-50 border-green-100",
    MOYEN:    "text-orange-600 bg-orange-50 border-orange-100",
    ELEVE:    "text-red-600 bg-red-50 border-red-100",
    CRITIQUE: "text-red-800 bg-red-100 border-red-200",
  };

  const COULEURS_DECISION: Record<string, string> = {
    FAVORABLE:    "text-green-600 bg-green-50 border-green-100",
    CONDITIONNEL: "text-orange-600 bg-orange-50 border-orange-100",
    DEFAVORABLE:  "text-red-600 bg-red-50 border-red-100",
  };

  const formaterMontant = (v: number) =>
    new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

  const Info = ({ label, valeur }: { label: string; valeur: string | number }) => (
    <div className="flex flex-col gap-0.5">
      <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="text-sm text-gray-700">{valeur}</p>
    </div>
  );

  const Section = ({ titre, children }: { titre: string; children: React.ReactNode }) => (
    <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-50">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
          {titre}
        </h2>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );

  return (
    <MainLayout titre={`Dossier #${String(id).padStart(5, "0")}`}>
      <div className="space-y-4">

        {/* Barre d'actions */}
        <div className="flex items-center justify-between">
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
          <button
            onClick={async () => {
              const token = useAuthStore.getState().accessToken;
              const reponse = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/rapports/${id}/`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              const blob = await reponse.blob();
              const url  = window.URL.createObjectURL(blob);
              const lien = document.createElement("a");
              lien.href = url;
              lien.download = `dossier-${id}.pdf`;
              lien.click();
              window.URL.revokeObjectURL(url);
            }}
            className="h-9 px-4 flex items-center gap-2 text-sm border
                       border-gray-200 rounded-lg text-gray-600
                       hover:bg-gray-50 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
              viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Télécharger PDF
          </button>

          {(dossier.statut === "BROUILLON" || dossier.statut === "DOCUMENTS_INCOMPLETS") && (
            <div className="flex gap-3">
              <button
                onClick={async () => {
                  const res = await dossiersService.soumettre(dossier.id);
                  alert(`Dossier soumis — score : ${res.score}/100`);
                  router.refresh();
                }}
                className="h-9 px-4 rounded-lg text-sm font-medium text-white"
                style={{ background: "var(--color-brand)" }}
              >
                Soumettre à nouveau
              </button>
              <button
                onClick={async () => {
                  if (!confirm("Supprimer définitivement ce dossier ?")) return;
                  await dossiersService.supprimer(dossier.id);
                  router.push("/dossiers");
                }}
                className="h-9 px-4 rounded-lg text-sm border border-red-200 text-red-600 hover:bg-red-50"
              >
                Supprimer
              </button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-3 gap-4">

          {/* Colonne principale */}
          <div className="col-span-2 space-y-4">

            <Section titre="Fiche 1 — Informations du client">
              <div className="grid grid-cols-3 gap-4">
                <Info label="Nom complet"
                  valeur={`${d.client.civilite}. ${d.client.nom} ${d.client.prenom}`} />
                <Info label="Date de naissance"
                  valeur={new Date(d.client.date_naissance).toLocaleDateString("fr-FR")} />
                <Info label="CNI"           valeur={d.client.numero_cni}    />
                <Info label="Téléphone"     valeur={d.client.telephone}     />
                <Info label="Email"         valeur={d.client.email || "—"}  />
                <Info label="Adresse"       valeur={d.client.adresse}       />
                <Info label="Employeur"     valeur={d.client.nom_employeur} />
                <Info label="Type"          valeur={d.client.type_employeur}/>
                <Info label="Poste"         valeur={d.client.poste_occupe}  />
                <Info label="Ancienneté"    valeur={`${d.client.anciennete} ans`} />
                <Info label="Salaire net"   valeur={formaterMontant(d.client.salaire_net)} />
                <Info label="Charges"       valeur={formaterMontant(d.client.charges_mensuelles)} />
              </div>
            </Section>

            <Section titre="Fiche 2 — Appréciation commerciale">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <Info label="Type de crédit"      valeur={d.type_credit_display}    />
                <Info label="Montant sollicité"   valeur={formaterMontant(d.montant_sollicite)} />
                <Info label="Durée"               valeur={`${d.duree_mois} mois`}   />
                <Info label="Mensualité estimée"  valeur={formaterMontant(d.mensualite_estimee)} />
                <Info label="Traite max autorisée" valeur={formaterMontant(d.traite_max_autorisee)} />
                <Info label="Taux d'endettement"  valeur={`${d.taux_endettement}%`} />
              </div>
              <div className="border-t border-gray-50 pt-4 space-y-2">
                <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">
                  Objet du financement
                </p>
                <p className="text-sm text-gray-700">{d.objet_financement}</p>
                <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wide mt-3">
                  Appréciation du commercial
                </p>
                <p className="text-sm text-gray-700">{d.appreciation}</p>
              </div>
            </Section>

            <Section titre="Circuit de validation">
              {d.validations?.length === 0 ? (
                <p className="text-sm text-gray-400">
                  Aucune validation enregistrée.
                </p>
              ) : (
                <div className="space-y-3">
                  {d.validations?.map((v: any, i: number) => (
                    <div key={i}
                      className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-8 h-8 rounded-full flex items-center
                                      justify-center bg-white border border-gray-100
                                      shrink-0 text-xs font-semibold"
                        style={{ color: "var(--color-brand)" }}>
                        {v.validateur[0]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-medium text-gray-700">
                            {v.validateur}
                          </p>
                          <span className={`text-[11px] font-medium px-2 py-0.5
                                            rounded-full ${
                            v.decision === "Approuvé"
                              ? "bg-green-50 text-green-600"
                              : "bg-red-50 text-red-600"
                          }`}>
                            {v.decision}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-400">
                          {v.role} · {v.date}
                        </p>
                        {v.commentaire && (
                          <p className="text-xs text-gray-600 mt-1">
                            {v.commentaire}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Section>

          </div>

          {/* Score IA */}
          <div className="space-y-4">
            <div className="bg-white border border-gray-100 rounded-xl p-5 space-y-4">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
                Score IA
              </h2>

              {score ? (
                <>
                  <div className="flex flex-col items-center gap-3">
                    <JaugeScore score={score.score} niveauRisque={score.niveau_risque} taille={112} />

                    <span className={`text-[11px] font-medium px-2.5 py-1
                                      rounded-full border
                                      ${COULEURS_DECISION[score.decision_ia]}`}>
                      {score.decision_ia_display}
                    </span>
                  </div>
                </>
              ) : (
                <p className="text-sm text-gray-400 text-center py-4">
                  Score non encore calculé.
                </p>
              )}
            </div>

            {score?.recommandation && (
              <div className="bg-white border border-gray-100 rounded-xl p-5">
                <h2 className="text-xs font-semibold text-gray-500 uppercase
                               tracking-widest mb-3">
                  Recommandation IA
                </h2>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {score.recommandation}
                </p>
              </div>
            )}

            {score?.conditions && (
              <div className="bg-orange-50 border border-orange-100 rounded-xl p-5">
                <h2 className="text-xs font-semibold text-orange-600 uppercase
                               tracking-widest mb-3">
                  Conditions proposées
                </h2>
                <p className="text-xs text-orange-700 leading-relaxed">
                  {score.conditions}
                </p>
              </div>
            )}

            {d.necessite_comite && (
              <div className="bg-pink-50 border border-pink-100 rounded-xl p-4">
                <p className="text-xs font-semibold text-pink-600 mb-1">
                  Passage en comité requis
                </p>
                <p className="text-[11px] text-pink-500">
                  Montant supérieur à 5 000 000 FCFA.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}