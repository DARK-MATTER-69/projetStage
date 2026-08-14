"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import MainLayout from "@/components/layout/MainLayout";
import { clientsService } from "@/services/clientsService";
import { dossiersService } from "@/services/dossiersService";

type Etape = 1 | 2 | 3;

interface DonneesClient {
  civilite:               string;
  nom:                    string;
  prenom:                 string;
  date_naissance:         string;
  lieu_naissance:         string;
  nationalite:            string;
  numero_cni:             string;
  telephone:              string;
  email:                  string;
  adresse:                string;
  type_employeur:         string;
  nom_employeur:          string;
  poste_occupe:           string;
  anciennete:             string;
  salaire_net:            string;
  charges_mensuelles:     string;
  credits_en_cours:       string;
  date_versement_salaire: string;
}

interface DonneesDossier {
  type_credit:            string;
  montant_sollicite:      string;
  duree_mois:             string;
  objet_financement:      string;
  appreciation:           string;
  date_debut_prelevement: string;
  jour_prelevement:       string;
  // ── Fiche 2 réelle SCE ──────────────────────────────────
  echeance_mens_banque:   string;
  encours_sce:            string;
  assureur:               string;
  montant_assurance_ttc:  string;
  avi:                    boolean;
  delegation_salaire:     boolean;
}

const ETAPES = [
  { num: 1, label: "Fiche client",        description: "Informations du demandeur"     },
  { num: 2, label: "Fiche appréciation",  description: "Détails de la demande"         },
  { num: 3, label: "Documents",           description: "Pièces justificatives"         },
];

/** Champ de formulaire réutilisable */
function Champ({
  label,
  required = false,
  children,
}: {
  label:     string;
  required?: boolean;
  children:  React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 uppercase
                         tracking-wide mb-1.5">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputClass = `w-full h-10 border border-gray-200 rounded-lg px-3 text-sm
                    text-gray-700 placeholder:text-gray-400 bg-white
                    focus:outline-none focus:border-[#922b00]
                    focus:ring-2 focus:ring-[#922b00]/10`;

const selectClass = `w-full h-10 border border-gray-200 rounded-lg px-3 text-sm
                     text-gray-700 bg-white
                     focus:outline-none focus:border-[#922b00]
                     focus:ring-2 focus:ring-[#922b00]/10`;

export default function NouveauDossierPage() {
  const router          = useRouter();
  const [etape, setEtape] = useState<Etape>(1);

  const [client, setClient] = useState<DonneesClient>({
    civilite:               "M",
    nom:                    "",
    prenom:                 "",
    date_naissance:         "",
    lieu_naissance:         "",
    nationalite:            "Camerounaise",
    numero_cni:             "",
    telephone:              "",
    email:                  "",
    adresse:                "",
    type_employeur:         "",
    nom_employeur:          "",
    poste_occupe:           "",
    anciennete:             "",
    salaire_net:            "",
    charges_mensuelles:     "0",
    credits_en_cours:       "0",
    date_versement_salaire: "",
  });

  const [dossier, setDossier] = useState<DonneesDossier>({
    type_credit:            "",
    montant_sollicite:      "",
    duree_mois:             "",
    objet_financement:      "",
    appreciation:           "",
    date_debut_prelevement: "",
    jour_prelevement:       "",
    echeance_mens_banque:   "0",
    encours_sce:            "0",
    assureur:               "",
    montant_assurance_ttc:  "0",
    avi:                    false,
    delegation_salaire:     false,
  });

  const [documents, setDocuments] = useState<Record<string, File | null>>({
    CNI:               null,
    RIB:               null,
    HISTORIQUE_BANQUE: null,
    NIU:               null,
  });

  const [chargement, setChargement] = useState(false);
  const [erreur,     setErreur]     = useState("");

  const majClient  = (champ: keyof DonneesClient,  val: string) =>
    setClient((prev) => ({ ...prev, [champ]: val }));

  const majDossier = (champ: keyof DonneesDossier, val: string | boolean) =>
    setDossier((prev) => ({ ...prev, [champ]: val }));

  // Calculs en temps réel
  const salaire          = parseFloat(client.salaire_net)          || 0;
  const charges          = parseFloat(client.charges_mensuelles)   || 0;
  const creditsEnCours   = parseFloat(client.credits_en_cours)     || 0;
  const montant          = parseFloat(dossier.montant_sollicite)   || 0;
  const duree            = parseFloat(dossier.duree_mois)          || 1;
  const echeanceBanque   = parseFloat(dossier.echeance_mens_banque) || 0;
  const mensualite       = montant / duree;
  const traiteMax        = salaire * 0.33 - creditsEnCours;
  const tauxEndettement  = salaire > 0 ? ((charges + mensualite) / salaire) * 100 : 0;
  const quotiteRelative  = salaire > 0 ? ((echeanceBanque + mensualite) / salaire) * 100 : 0;
  const necessite_comite = montant > 5_000_000;

  const handleSoumettre = async () => {
  setChargement(true);
  setErreur("");

  try {
    // Étape 1 — Créer le client (Fiche 1)
    const clientData = await clientsService.creer({
      civilite:               client.civilite,
      nom:                    client.nom,
      prenom:                 client.prenom,
      date_naissance:         client.date_naissance,
      lieu_naissance:         client.lieu_naissance,
      nationalite:            client.nationalite,
      numero_cni:             client.numero_cni,
      telephone:              client.telephone,
      email:                  client.email,
      adresse:                client.adresse,
      type_employeur:         client.type_employeur,
      nom_employeur:          client.nom_employeur,
      poste_occupe:           client.poste_occupe,
      anciennete:             Number(client.anciennete),
      salaire_net:            Number(client.salaire_net),
      charges_mensuelles:     Number(client.charges_mensuelles),
      credits_en_cours:       Number(client.credits_en_cours),
      date_versement_salaire: Number(client.date_versement_salaire),
    });

    // Étape 2 — Créer le dossier (Fiche 2)
    const dossierData = await dossiersService.creer({
      client_id:              clientData.id,
      type_credit:            dossier.type_credit,
      montant_sollicite:      Number(dossier.montant_sollicite),
      duree_mois:             Number(dossier.duree_mois),
      objet_financement:      dossier.objet_financement,
      appreciation:           dossier.appreciation,
      date_debut_prelevement: dossier.date_debut_prelevement,
      jour_prelevement:       Number(dossier.jour_prelevement),
      echeance_mens_banque:   Number(dossier.echeance_mens_banque),
      encours_sce:            Number(dossier.encours_sce),
      assureur:               dossier.assureur,
      montant_assurance_ttc:  Number(dossier.montant_assurance_ttc),
      avi:                    dossier.avi,
      delegation_salaire:     dossier.delegation_salaire,
    });

    // Étape 3 — Uploader les documents
    const uploads = Object.entries(documents).filter(([, fichier]) => fichier !== null);

    for (const [typeDoc, fichier] of uploads) {
      if (fichier) {
        await dossiersService.uploaderDocument(
          dossierData.id,
          typeDoc,
          fichier
        );
      }
    }

    // Étape 4 — Soumettre le dossier (déclenche le scoring IA)
    await dossiersService.soumettre(dossierData.id);

    // Redirection vers le détail du dossier créé
    router.push(`/dossiers/${dossierData.id}`);

  } catch (err: unknown) {
    const error = err as { response?: { data?: Record<string, string[]> } };
    if (error.response?.data) {
      const messages = Object.values(error.response.data).flat();
      setErreur(messages[0] || "Une erreur est survenue.");
    } else {
      setErreur("Une erreur est survenue. Vérifiez votre connexion.");
    }
  } finally {
    setChargement(false);
  }
};

  return (
    <MainLayout titre="Nouveau dossier de crédit">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* Indicateur d'étapes */}
        <div className="bg-white border border-gray-100 rounded-xl p-5">
          <div className="flex items-center gap-0">
            {ETAPES.map((e, i) => (
              <div key={e.num} className="flex items-center flex-1">
                <button
                  onClick={() => etape > e.num && setEtape(e.num as Etape)}
                  className="flex items-center gap-3 group"
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center
                                   text-sm font-semibold flex-shrink-0 transition-colors
                                   ${etape === e.num
                                     ? "text-white"
                                     : etape > e.num
                                       ? "text-white"
                                       : "bg-gray-100 text-gray-400"
                                   }`}
                    style={
                      etape === e.num || etape > e.num
                        ? { background: "#922b00" }
                        : {}
                    }
                  >
                    {etape > e.num ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    ) : e.num}
                  </div>
                  <div className="text-left hidden sm:block">
                    <p className={`text-xs font-medium ${etape === e.num ? "text-gray-800" : "text-gray-400"}`}>
                      {e.label}
                    </p>
                    <p className="text-[10px] text-gray-400">{e.description}</p>
                  </div>
                </button>
                {i < ETAPES.length - 1 && (
                  <div className={`flex-1 h-px mx-4 ${etape > e.num ? "bg-[#922b00]" : "bg-gray-100"}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ── ETAPE 1 — Fiche client ── */}
        {etape === 1 && (
          <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-6">
            <h2 className="text-sm font-semibold text-gray-800 border-b border-gray-50 pb-3">
              Fiche 1 — Informations du client
            </h2>

            {/* Identité */}
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
                Identité
              </p>
              <div className="grid grid-cols-2 gap-4">
                <Champ label="Civilité" required>
                  <select
                    value={client.civilite}
                    onChange={(e) => majClient("civilite", e.target.value)}
                    className={selectClass}
                  >
                    <option value="M">Monsieur</option>
                    <option value="MME">Madame</option>
                  </select>
                </Champ>
                <Champ label="Nom" required>
                  <input type="text" value={client.nom}
                    onChange={(e) => majClient("nom", e.target.value)}
                    placeholder="Nom de famille"
                    className={inputClass} />
                </Champ>
                <Champ label="Prénom" required>
                  <input type="text" value={client.prenom}
                    onChange={(e) => majClient("prenom", e.target.value)}
                    placeholder="Prénom"
                    className={inputClass} />
                </Champ>
                <Champ label="Date de naissance" required>
                  <input type="date" value={client.date_naissance}
                    onChange={(e) => majClient("date_naissance", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Lieu de naissance" required>
                  <input type="text" value={client.lieu_naissance}
                    onChange={(e) => majClient("lieu_naissance", e.target.value)}
                    placeholder="Ville de naissance"
                    className={inputClass} />
                </Champ>
                <Champ label="Nationalité" required>
                  <input type="text" value={client.nationalite}
                    onChange={(e) => majClient("nationalite", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Numéro CNI" required>
                  <input type="text" value={client.numero_cni}
                    onChange={(e) => majClient("numero_cni", e.target.value)}
                    placeholder="N° de la CNI"
                    className={inputClass} />
                </Champ>
                <Champ label="Téléphone" required>
                  <input type="tel" value={client.telephone}
                    onChange={(e) => majClient("telephone", e.target.value)}
                    placeholder="6XXXXXXXX"
                    className={inputClass} />
                </Champ>
                <Champ label="Email">
                  <input type="email" value={client.email}
                    onChange={(e) => majClient("email", e.target.value)}
                    placeholder="email@exemple.com"
                    className={inputClass} />
                </Champ>
                <Champ label="Adresse" required>
                  <input type="text" value={client.adresse}
                    onChange={(e) => majClient("adresse", e.target.value)}
                    placeholder="Quartier, ville"
                    className={inputClass} />
                </Champ>
              </div>
            </div>

            {/* Situation professionnelle */}
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
                Situation professionnelle
              </p>
              <div className="grid grid-cols-2 gap-4">
                <Champ label="Type d'employeur" required>
                  <select value={client.type_employeur}
                    onChange={(e) => majClient("type_employeur", e.target.value)}
                    className={selectClass}>
                    <option value="">Sélectionner</option>
                    <option value="FONCTIONNAIRE">Fonctionnaire</option>
                    <option value="PRIVE">Secteur privé</option>
                    <option value="ONG">ONG / Association</option>
                    <option value="COMMERCANT">Commerçant</option>
                    <option value="RETRAITE">Retraité</option>
                    <option value="AUTRE">Autre</option>
                  </select>
                </Champ>
                <Champ label="Nom de l'employeur" required>
                  <input type="text" value={client.nom_employeur}
                    onChange={(e) => majClient("nom_employeur", e.target.value)}
                    placeholder="Nom de la structure"
                    className={inputClass} />
                </Champ>
                <Champ label="Poste occupé" required>
                  <input type="text" value={client.poste_occupe}
                    onChange={(e) => majClient("poste_occupe", e.target.value)}
                    placeholder="Intitulé du poste"
                    className={inputClass} />
                </Champ>
                <Champ label="Ancienneté (années)" required>
                  <input type="number" min="0" value={client.anciennete}
                    onChange={(e) => majClient("anciennete", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
              </div>
            </div>

            {/* Situation financière */}
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
                Situation financière
              </p>
              <div className="grid grid-cols-2 gap-4">
                <Champ label="Salaire net mensuel (FCFA)" required>
                  <input type="number" min="0" value={client.salaire_net}
                    onChange={(e) => majClient("salaire_net", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Charges mensuelles (FCFA)">
                  <input type="number" min="0" value={client.charges_mensuelles}
                    onChange={(e) => majClient("charges_mensuelles", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Crédits en cours (FCFA)">
                  <input type="number" min="0" value={client.credits_en_cours}
                    onChange={(e) => majClient("credits_en_cours", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Jour de versement du salaire">
                  <input type="number" min="1" max="31"
                    value={client.date_versement_salaire}
                    onChange={(e) => majClient("date_versement_salaire", e.target.value)}
                    placeholder="Ex : 25"
                    className={inputClass} />
                </Champ>
              </div>
            </div>
          </div>
        )}

        {/* ── ETAPE 2 — Fiche appréciation ── */}
        {etape === 2 && (
          <div className="space-y-4">
            <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-5">
              <h2 className="text-sm font-semibold text-gray-800 border-b border-gray-50 pb-3">
                Fiche 2 — Appréciation commerciale
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <Champ label="Type de crédit" required>
                  <select value={dossier.type_credit}
                    onChange={(e) => majDossier("type_credit", e.target.value)}
                    className={selectClass}>
                    <option value="">Sélectionner</option>
                    <option value="EQUIPEMENT">Crédit équipement</option>
                    <option value="SCOLAIRE">Crédit scolaire</option>
                    <option value="BAIL">Crédit-bail</option>
                    <option value="CONSOMMATION">Crédit consommation</option>
                    <option value="AUTRE">Autre</option>
                  </select>
                </Champ>
                <Champ label="Montant sollicité (FCFA)" required>
                  <input type="number" min="0" value={dossier.montant_sollicite}
                    onChange={(e) => majDossier("montant_sollicite", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Durée (mois)" required>
                  <select value={dossier.duree_mois}
                    onChange={(e) => majDossier("duree_mois", e.target.value)}
                    className={selectClass}>
                    <option value="">Sélectionner</option>
                    {[6, 12, 18, 24, 36, 48, 60].map((m) => (
                      <option key={m} value={m}>{m} mois</option>
                    ))}
                  </select>
                </Champ>
                <Champ label="Date début prélèvement" required>
                  <input type="date" value={dossier.date_debut_prelevement}
                    onChange={(e) => majDossier("date_debut_prelevement", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Jour de prélèvement mensuel" required>
                  <input type="number" min="1" max="28"
                    value={dossier.jour_prelevement}
                    onChange={(e) => majDossier("jour_prelevement", e.target.value)}
                    placeholder="Ex : 28"
                    className={inputClass} />
                </Champ>
              </div>

              <Champ label="Objet du financement" required>
                <input type="text" value={dossier.objet_financement}
                  onChange={(e) => majDossier("objet_financement", e.target.value)}
                  placeholder="Décrire l'objet du crédit"
                  className={inputClass} />
              </Champ>

              <Champ label="Appréciation du commercial" required>
                <textarea
                  value={dossier.appreciation}
                  onChange={(e) => majDossier("appreciation", e.target.value)}
                  rows={4}
                  placeholder="Observations sur le client et le dossier..."
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5
                             text-sm text-gray-700 placeholder:text-gray-400
                             focus:outline-none focus:border-[#922b00]
                             focus:ring-2 focus:ring-[#922b00]/10 resize-none"
                />
              </Champ>
            </div>

            {/* Données SCE — engagements existants */}
            <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-5">
              <h2 className="text-sm font-semibold text-gray-800 border-b border-gray-50 pb-3">
                Données SCE — Engagements existants
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <Champ label="Echéance mensuelle banque (FCFA)">
                  <input type="number" min="0" value={dossier.echeance_mens_banque}
                    onChange={(e) => majDossier("echeance_mens_banque", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Encours SCE (FCFA)">
                  <input type="number" min="0" value={dossier.encours_sce}
                    onChange={(e) => majDossier("encours_sce", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Assureur">
                  <input type="text" value={dossier.assureur}
                    onChange={(e) => majDossier("assureur", e.target.value)}
                    placeholder="Nom de l'assureur"
                    className={inputClass} />
                </Champ>
                <Champ label="Montant assurance TTC (FCFA)">
                  <input type="number" min="0" value={dossier.montant_assurance_ttc}
                    onChange={(e) => majDossier("montant_assurance_ttc", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
              </div>

              <div className="flex items-center gap-6 pt-1">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={dossier.avi}
                    onChange={(e) => majDossier("avi", e.target.checked)}
                    className="w-4 h-4 accent-[#922b00]" />
                  AVI
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={dossier.delegation_salaire}
                    onChange={(e) => majDossier("delegation_salaire", e.target.checked)}
                    className="w-4 h-4 accent-[#922b00]" />
                  Délégation de salaire
                </label>
              </div>
            </div>

            {/* Résumé financier temps réel */}
            {salaire > 0 && montant > 0 && (
              <div className="bg-white border border-gray-100 rounded-xl p-5">
                <h3 className="text-xs font-semibold text-gray-500 uppercase
                               tracking-widest mb-4">
                  Résumé financier
                </h3>
                <div className="grid grid-cols-4 gap-4">
                  {[
                    {
                      label: "Mensualité estimée",
                      valeur: new Intl.NumberFormat("fr-FR").format(Math.round(mensualite)) + " FCFA",
                      ok:     mensualite <= traiteMax,
                    },
                    {
                      label: "Traite max autorisée",
                      valeur: new Intl.NumberFormat("fr-FR").format(Math.round(traiteMax)) + " FCFA",
                      ok:     true,
                    },
                    {
                      label: "Quotité relative",
                      valeur: quotiteRelative.toFixed(1) + "%",
                      ok:     quotiteRelative <= 33,
                    },
                    {
                      label: "Passage en comité",
                      valeur: necessite_comite ? "Requis" : "Non requis",
                      ok:     !necessite_comite,
                    },
                  ].map(({ label, valeur, ok }) => (
                    <div key={label}
                      className={`p-3 rounded-lg border ${
                        ok ? "border-green-100 bg-green-50" : "border-red-100 bg-red-50"
                      }`}>
                      <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">
                        {label}
                      </p>
                      <p className={`text-sm font-semibold ${ok ? "text-green-700" : "text-red-600"}`}>
                        {valeur}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── ETAPE 3 — Documents ── */}
        {etape === 3 && (
          <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-4">
            <h2 className="text-sm font-semibold text-gray-800 border-b border-gray-50 pb-3">
              Documents justificatifs
            </h2>
            <p className="text-xs text-gray-400">
              Scannez et uploadez les documents remis par le client.
            </p>

            {[
              { key: "CNI",               label: "Photocopie CNI",                  required: true  },
              { key: "RIB",               label: "Relevé d'identité bancaire (RIB)", required: true  },
              { key: "HISTORIQUE_BANQUE", label: "Historique de compte (3 mois)",    required: true  },
              { key: "NIU",               label: "Attestation d'immatriculation (NIU)", required: true },
            ].map(({ key, label, required }) => (
              <div key={key}
                className="flex items-center justify-between p-4 border border-gray-100
                           rounded-lg hover:border-[#922b00]/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center
                                   ${documents[key] ? "bg-green-50" : "bg-gray-50"}`}>
                    {documents[key] ? (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"
                        viewBox="0 0 24 24" fill="none" stroke="#16a34a"
                        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"
                        viewBox="0 0 24 24" fill="none" stroke="#9ca3af"
                        strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-gray-700 font-medium">
                      {label}
                      {required && <span className="text-red-400 ml-0.5">*</span>}
                    </p>
                    <p className="text-[11px] text-gray-400">
                      {documents[key] ? documents[key]!.name : "Aucun fichier sélectionné"}
                    </p>
                  </div>
                </div>

                <label className="cursor-pointer text-xs font-medium px-3 py-1.5
                                   border border-[#922b00] text-[#922b00] rounded-lg
                                   hover:bg-[#922b00] hover:text-white transition-all">
                  {documents[key] ? "Remplacer" : "Choisir"}
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                    onChange={(e) => {
                      const fichier = e.target.files?.[0] || null;
                      setDocuments((prev) => ({ ...prev, [key]: fichier }));
                    }}
                  />
                </label>
              </div>
            ))}

            {erreur && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200
                            rounded px-3 py-2">
                {erreur}
              </p>
            )}
          </div>
        )}

        {/* Navigation entre étapes */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setEtape((prev) => (prev - 1) as Etape)}
            disabled={etape === 1}
            className="h-10 px-5 border border-gray-200 rounded-lg text-sm
                       text-gray-600 hover:bg-gray-50 disabled:opacity-30
                       disabled:cursor-not-allowed transition-all"
          >
            ← Précédent
          </button>

          {etape < 3 ? (
            <button
              onClick={() => setEtape((prev) => (prev + 1) as Etape)}
              className="h-10 px-5 rounded-lg text-sm font-medium text-white
                         transition-all"
              style={{ background: "#922b00" }}
            >
              Suivant →
            </button>
          ) : (
            <button
              onClick={handleSoumettre}
              disabled={chargement}
              className="h-10 px-5 rounded-lg text-sm font-medium text-white
                         disabled:opacity-50 transition-all flex items-center gap-2"
              style={{ background: "#922b00" }}
            >
              {chargement ? "Soumission..." : "Soumettre le dossier"}
            </button>
          )}
        </div>

      </div>
    </MainLayout>
  );
}