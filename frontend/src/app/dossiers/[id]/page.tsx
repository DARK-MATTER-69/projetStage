"use client";

import { useParams, useRouter } from "next/navigation";
import MainLayout from "@/components/layout/MainLayout";

interface Validation {
  validateur:  string;
  role:        string;
  decision:    string;
  commentaire: string;
  date:        string;
}

interface Score {
  score:                        number;
  niveau_risque:                string;
  decision_ia:                  string;
  taux_endettement:             number;
  ratio_mensualite_salaire:     number;
  delai_securite:               number;
  score_stabilite_emploi:       number;
  score_capacite_remboursement: number;
  score_profil_client:          number;
  score_dossier:                number;
  recommandation_ia:            string;
  conditions_proposees:         string;
}

interface DossierDetail {
  id:                  number;
  client: {
    civilite:          string;
    nom:               string;
    prenom:            string;
    date_naissance:    string;
    numero_cni:        string;
    telephone:         string;
    email:             string;
    adresse:           string;
    type_employeur:    string;
    nom_employeur:     string;
    poste_occupe:      string;
    anciennete:        number;
    salaire_net:       number;
    charges_mensuelles: number;
    credits_en_cours:  number;
  };
  type_credit:          string;
  montant_sollicite:    number;
  duree_mois:           number;
  objet_financement:    string;
  appreciation:         string;
  statut:               string;
  necessite_comite:     boolean;
  mensualite_estimee:   number;
  taux_endettement:     number;
  traite_max_autorisee: number;
  est_traite_acceptable: boolean;
  validations:          Validation[];
  score:                Score;
  cree_le:              string;
}

// Données de démonstration
const DOSSIER_DEMO: DossierDetail = {
  id: 1,
  client: {
    civilite:           "M",
    nom:                "Mbarga",
    prenom:             "Jean-Pierre",
    date_naissance:     "1985-03-15",
    numero_cni:         "123456789",
    telephone:          "677123456",
    email:              "mbarga.jp@email.com",
    adresse:            "Bastos, Yaoundé",
    type_employeur:     "Fonctionnaire",
    nom_employeur:      "Ministère des Finances",
    poste_occupe:       "Cadre",
    anciennete:         8,
    salaire_net:        250000,
    charges_mensuelles: 30000,
    credits_en_cours:   0,
  },
  type_credit:          "Équipement",
  montant_sollicite:    850000,
  duree_mois:           12,
  objet_financement:    "Achat téléviseur et climatiseur",
  appreciation:         "Client sérieux avec 8 ans d'ancienneté. Dossier complet et conforme.",
  statut:               "EN_ANALYSE",
  necessite_comite:     false,
  mensualite_estimee:   70833,
  taux_endettement:     28.3,
  traite_max_autorisee: 82500,
  est_traite_acceptable: true,
  validations: [
    {
      validateur:  "Dupont Chef",
      role:        "Chef d'agence",
      decision:    "Approuvé",
      commentaire: "Dossier conforme, transmis pour analyse.",
      date:        "2025-08-07 10:30",
    },
  ],
  score: {
    score:                        74,
    niveau_risque:                "MOYEN",
    decision_ia:                  "FAVORABLE",
    taux_endettement:             28.3,
    ratio_mensualite_salaire:     28.3,
    delai_securite:               3,
    score_stabilite_emploi:       22,
    score_capacite_remboursement: 18,
    score_profil_client:          19,
    score_dossier:                15,
    recommandation_ia:            "Le profil du client présente une bonne stabilité professionnelle en tant que fonctionnaire avec 8 ans d'ancienneté. Le taux d'endettement de 28,3% reste en dessous du seuil COBAC de 33%. La décision est favorable sous réserve de vérification des documents.",
    conditions_proposees:         "",
  },
  cree_le: "2025-08-08",
};

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

/** Ligne d'information */
function Info({ label, valeur }: { label: string; valeur: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="text-sm text-gray-700">{valeur}</p>
    </div>
  );
}

/** Section avec titre */
function Section({ titre, children }: { titre: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-50">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
          {titre}
        </h2>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

export default function DetailDossierPage() {
  const params  = useParams();
  const router  = useRouter();
  const d       = DOSSIER_DEMO;
  const score   = d.score;

  const jaugeScore = (score.score / 100) * 100;
  const couleurJauge =
    score.score >= 70 ? "#16a34a" :
    score.score >= 50 ? "#ea580c" : "#dc2626";

  return (
    <MainLayout titre={`Dossier #${String(params.id).padStart(5, "0")}`}>
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

          <div className="flex items-center gap-2">
            
              href={`/api/rapports/${params.id}/`}
              target="_blank"
              className="h-9 px-4 flex items-center gap-2 text-sm border
                         border-gray-200 rounded-lg text-gray-600
                         hover:bg-gray-50 transition-colors"
            </div>
            <a>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              Télécharger PDF
            </a>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">

          {/* Colonne principale */}
          <div className="col-span-2 space-y-4">

            {/* Informations client */}
            <Section titre="Fiche 1 — Informations du client">
              <div className="grid grid-cols-3 gap-4">
                <Info label="Nom complet"
                  valeur={`${d.client.civilite}. ${d.client.nom} ${d.client.prenom}`} />
                <Info label="Date de naissance"
                  valeur={new Date(d.client.date_naissance).toLocaleDateString("fr-FR")} />
                <Info label="CNI"           valeur={d.client.numero_cni}   />
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

            {/* Détails du crédit */}
            <Section titre="Fiche 2 — Appréciation commerciale">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <Info label="Type de crédit"    valeur={d.type_credit}      />
                <Info label="Montant sollicité" valeur={formaterMontant(d.montant_sollicite)} />
                <Info label="Durée"             valeur={`${d.duree_mois} mois`} />
                <Info label="Mensualité estimée" valeur={formaterMontant(d.mensualite_estimee)} />
                <Info label="Traite max autorisée" valeur={formaterMontant(d.traite_max_autorisee)} />
                <Info label="Taux d'endettement" valeur={`${d.taux_endettement}%`} />
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

            {/* Circuit de validation */}
            <Section titre="Circuit de validation">
              {d.validations.length === 0 ? (
                <p className="text-sm text-gray-400">Aucune validation enregistrée.</p>
              ) : (
                <div className="space-y-3">
                  {d.validations.map((v, i) => (
                    <div key={i}
                      className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-8 h-8 rounded-full flex items-center
                                      justify-content-center bg-white border border-gray-100
                                      flex-shrink-0 flex items-center justify-center
                                      text-xs font-semibold"
                        style={{ color: "#922b00" }}>
                        {v.validateur[0]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-medium text-gray-700">
                            {v.validateur}
                          </p>
                          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full
                                            ${v.decision === "Approuvé"
                                              ? "bg-green-50 text-green-600"
                                              : "bg-red-50 text-red-600"}`}>
                            {v.decision}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-400">{v.role} · {v.date}</p>
                        {v.commentaire && (
                          <p className="text-xs text-gray-600 mt-1">{v.commentaire}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Section>

          </div>

          {/* Colonne latérale — Score IA */}
          <div className="space-y-4">

            {/* Score global */}
            <div className="bg-white border border-gray-100 rounded-xl p-5 space-y-4">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
                Score IA
              </h2>

              {/* Jauge circulaire */}
              <div className="flex flex-col items-center gap-3">
                <div className="relative w-28 h-28">
                  <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                    <circle cx="50" cy="50" r="40" fill="none"
                      stroke="#f3f4f6" strokeWidth="10" />
                    <circle cx="50" cy="50" r="40" fill="none"
                      stroke={couleurJauge} strokeWidth="10"
                      strokeDasharray={`${2 * Math.PI * 40 * jaugeScore / 100} ${2 * Math.PI * 40}`}
                      strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-gray-800">
                      {score.score}
                    </span>
                    <span className="text-[10px] text-gray-400">/ 100</span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full border
                                    ${COULEURS_RISQUE[score.niveau_risque]}`}>
                    {score.niveau_risque === "FAIBLE"   ? "Risque faible"   :
                     score.niveau_risque === "MOYEN"    ? "Risque moyen"    :
                     score.niveau_risque === "ELEVE"    ? "Risque élevé"    :
                     "Risque critique"}
                  </span>
                </div>

                <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full border
                                  ${COULEURS_DECISION[score.decision_ia]}`}>
                  Décision : {score.decision_ia === "FAVORABLE"    ? "Favorable"    :
                              score.decision_ia === "CONDITIONNEL" ? "Conditionnel" :
                              "Défavorable"}
                </span>
              </div>

              {/* Détail des critères */}
              <div className="space-y-2.5 border-t border-gray-50 pt-4">
                {[
                  { label: "Stabilité emploi",    val: score.score_stabilite_emploi,       max: 25 },
                  { label: "Capacité remb.",       val: score.score_capacite_remboursement, max: 25 },
                  { label: "Profil client",        val: score.score_profil_client,          max: 25 },
                  { label: "Dossier",              val: score.score_dossier,                max: 25 },
                ].map(({ label, val, max }) => (
                  <div key={label}>
                    <div className="flex justify-between text-[11px] text-gray-500 mb-1">
                      <span>{label}</span>
                      <span className="font-medium">{val}/{max}</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${(val / max) * 100}%`,
                          background: "#922b00",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommandation IA */}
            {score.recommandation_ia && (
              <div className="bg-white border border-gray-100 rounded-xl p-5">
                <h2 className="text-xs font-semibold text-gray-500 uppercase
                               tracking-widest mb-3">
                  Recommandation IA
                </h2>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {score.recommandation_ia}
                </p>
              </div>
            )}

            {/* Conditions si conditionnel */}
            {score.conditions_proposees && (
              <div className="bg-orange-50 border border-orange-100 rounded-xl p-5">
                <h2 className="text-xs font-semibold text-orange-600 uppercase
                               tracking-widest mb-3">
                  Conditions proposées
                </h2>
                <p className="text-xs text-orange-700 leading-relaxed">
                  {score.conditions_proposees}
                </p>
              </div>
            )}

            {/* Alerte comité */}
            {d.necessite_comite && (
              <div className="bg-pink-50 border border-pink-100 rounded-xl p-4">
                <p className="text-xs font-semibold text-pink-600 mb-1">
                  Passage en comité requis
                </p>
                <p className="text-[11px] text-pink-500">
                  Montant supérieur à 5 000 000 FCFA.
                  Ce dossier nécessite l'accord du comité d'actionnaires.
                </p>
              </div>
            )}

          </div>
        </div>
      </div>
    </MainLayout>
  );
}