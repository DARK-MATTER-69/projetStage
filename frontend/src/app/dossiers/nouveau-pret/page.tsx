"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import MainLayout from "@/components/layout/MainLayout";
import JaugeScore from "@/components/ui/JaugeScore";
import { clientsService } from "@/services/clientsService";
import { dossiersService } from "@/services/dossiersService";

type Etape = "RECHERCHE" | "FORMULAIRE" | "RESULTAT";

interface DonneesPret {
  type_credit:            string;
  montant_sollicite:      string;
  duree_mois:             string;
  objet_financement:      string;
  appreciation:           string;
  date_debut_prelevement: string;
  jour_prelevement:       string;
  echeance_mens_banque:   string;
  encours_sce:            string;
  assureur:               string;
  montant_assurance_ttc:  string;
  avi:                    boolean;
  delegation_salaire:     boolean;
}

const inputClass = `w-full h-10 border border-gray-200 rounded-lg px-3 text-sm
                    text-gray-700 placeholder:text-gray-400 bg-white
                    focus:outline-none focus:border-[var(--color-brand)]
                    focus:ring-2 focus:ring-[var(--color-brand)]/10`;

const selectClass = `w-full h-10 border border-gray-200 rounded-lg px-3 text-sm
                     text-gray-700 bg-white
                     focus:outline-none focus:border-[var(--color-brand)]
                     focus:ring-2 focus:ring-[var(--color-brand)]/10`;

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

export default function NouveauPretPage() {
  const router = useRouter();

  const [etape,      setEtape]      = useState<Etape>("RECHERCHE");
  const [cni,        setCni]        = useState("");
  const [client,     setClient]     = useState<any>(null);
  const [candidats,  setCandidats]  = useState<any[]>([]);
  const [recherche,  setRecherche]  = useState(false);
  const [erreurRecherche, setErreurRecherche] = useState("");

  const [salaireModifie, setSalaireModifie] = useState(false);
  const [nouveauSalaire, setNouveauSalaire] = useState("");
 
  

  const [pret, setPret] = useState<DonneesPret>({
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

  const [chargement, setChargement] = useState(false);
  const [erreur,     setErreur]     = useState("");
  const [resultat,   setResultat]   = useState<{ score: number; niveau_risque: string; decision_ia: string; dossierId: number } | null>(null);

  const majPret = (champ: keyof DonneesPret, val: string | boolean) =>
    setPret((prev) => ({ ...prev, [champ]: val }));

  // Calculs en temps réel
  const salaireActuel   = Number(nouveauSalaire) || 0;
  const charges         = client ? Number(client.charges_mensuelles) : 0;
  const creditsEnCours  = client ? Number(client.credits_en_cours)   : 0;
  const montant         = parseFloat(pret.montant_sollicite)         || 0;
  const duree            = parseFloat(pret.duree_mois)               || 1;
  const echeanceBanque   = parseFloat(pret.echeance_mens_banque)     || 0;
  const mensualite        = montant / duree;
  const traiteMax         = salaireActuel * 0.33 - creditsEnCours;
  const quotiteRelative   = salaireActuel > 0 ? ((echeanceBanque + mensualite) / salaireActuel) * 100 : 0;
  const necessiteComite   = montant > 5_000_000;

  const handleRechercher = async () => {
    if (!cni.trim()) return;
    setRecherche(true);
    setErreurRecherche("");
    setCandidats([]);
    try {
      const resultats = await clientsService.rechercherParCni(cni.trim());
      if (resultats.length === 0) {
        setErreurRecherche("Aucun client trouvé avec ce numéro CNI.");
        setClient(null);
      } else if (resultats.length === 1) {
        selectionnerClient(resultats[0]);
      } else {
        setCandidats(resultats);
      }
    } catch {
      setErreurRecherche("Une erreur est survenue lors de la recherche.");
    } finally {
      setRecherche(false);
    }
  };

  const selectionnerClient = (c: any) => {
    setClient(c);
    setNouveauSalaire(String(c.salaire_net));
    setPret((prev) => ({
      ...prev,
      encours_sce: String(c.encours_sce_actuel ?? 0),
    }));
    setEtape("FORMULAIRE");
  };

  const handleSoumettre = async () => {
    if (!client) return;
    setChargement(true);
    setErreur("");

    try {
      // Si le salaire a été modifié, on passe par l'historique salarial
      // (traçabilité + recalcul automatique des scores existants du client)
      if (salaireModifie && Number(nouveauSalaire) !== client.salaire_net) {
        await clientsService.ajouterSalaire(client.id, {
          salaire:    Number(nouveauSalaire),
          date_effet: new Date().toISOString().slice(0, 10),
          note:       "Mise à jour lors d'une demande de nouveau prêt",
        });
      }

      // Création du dossier, directement rattaché au client existant
      const dossierData = await dossiersService.creer({
        client_id:              client.id,
        type_credit:            pret.type_credit,
        montant_sollicite:      Number(pret.montant_sollicite),
        duree_mois:             Number(pret.duree_mois),
        objet_financement:      pret.objet_financement,
        appreciation:           pret.appreciation,
        date_debut_prelevement: pret.date_debut_prelevement,
        jour_prelevement:       Number(pret.jour_prelevement),
        echeance_mens_banque:   Number(pret.echeance_mens_banque),
        encours_sce:            Number(pret.encours_sce),
        assureur:               pret.assureur,
        montant_assurance_ttc:  Number(pret.montant_assurance_ttc),
        avi:                    pret.avi,
        delegation_salaire:     pret.delegation_salaire,
      });

      // Pas de documents à uploader — le client est déjà connu
      const res = await dossiersService.soumettre(dossierData.id);

      setResultat({
        score:         res.score ?? 0,
        niveau_risque: res.niveau_risque ?? "",
        decision_ia:   res.decision_ia ?? "",
        dossierId:     dossierData.id,
      });
      setEtape("RESULTAT");

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
    <MainLayout titre="Nouveau prêt — Client existant">
      <p className="text-sm text-gray-500 mb-4">
        Pour un client déjà enregistré. Recherchez-le par son numéro CNI pour lui créer un nouveau dossier de crédit.
      </p>

      <div className="max-w-3xl mx-auto space-y-6">

        {/* ── ÉTAPE RECHERCHE ── */}
        {etape === "RECHERCHE" && (
          <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-4">
            <h2 className="text-sm font-semibold text-gray-800 border-b border-gray-50 pb-3">
              Retrouver le client
            </h2>
            <Champ label="Numéro CNI" required>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={cni}
                  onChange={(e) => setCni(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleRechercher()}
                  placeholder="Saisir le numéro de la CNI"
                  className={inputClass}
                />
                <button
                  onClick={handleRechercher}
                  disabled={recherche || !cni.trim()}
                  className="h-10 px-5 rounded-lg text-sm font-medium text-white
                             disabled:opacity-50 flex-shrink-0"
                  style={{ background: "var(--color-brand)" }}
                >
                  {recherche ? "Recherche..." : "Rechercher"}
                </button>
              </div>
            </Champ>
            {erreurRecherche && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200
                            rounded px-3 py-2">
                {erreurRecherche}
                {" — "}
                <a href="/dossiers/nouveau" className="underline">
                  Créer un nouveau dossier client
                </a>
              </p>
            )}
            
            {candidats.length > 1 && (
              <div className="space-y-2">
                <p className="text-xs text-gray-500">
                  Plusieurs clients correspondent — sélectionne le bon :
                </p>
                {candidats.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => selectionnerClient(c)}
                    className="w-full flex items-center justify-between p-3
                               border border-gray-100 rounded-lg text-left
                               hover:border-[var(--color-brand)]/40 transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {c.civilite_display} {c.nom} {c.prenom}
                      </p>
                      <p className="text-xs text-gray-400">CNI : {c.numero_cni}</p>
                    </div>
                    <span className="text-xs text-gray-400">{c.telephone}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}


        {/* ── ÉTAPE FORMULAIRE ── */}
        {etape === "FORMULAIRE" && client && (
          <div className="space-y-4">

            {/* Fiche client (lecture seule) */}
            <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                <h2 className="text-sm font-semibold text-gray-800">
                  {client.civilite_display} {client.nom} {client.prenom}
                </h2>
                <button
                  onClick={() => { setEtape("RECHERCHE"); setClient(null); setCni(""); }}
                  className="text-xs text-gray-400 hover:text-gray-700 underline"
                >
                  Ce n&apos;est pas le bon client ?
                </button>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide">CNI</p>
                  <p className="text-gray-700">{client.numero_cni}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide">Employeur</p>
                  <p className="text-gray-700">{client.nom_employeur}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wide">Ancienneté</p>
                  <p className="text-gray-700">{client.anciennete} ans</p>
                </div>
              </div>

              <Champ label="Salaire net mensuel (FCFA)" required>
                <input
                  type="number"
                  min="0"
                  value={nouveauSalaire}
                  onChange={(e) => {
                    setNouveauSalaire(e.target.value);
                    setSalaireModifie(Number(e.target.value) !== client.salaire_net);
                  }}
                  className={inputClass}
                />
                {salaireModifie && (
                  <p className="text-[11px] text-orange-600 mt-1">
                    Salaire modifié — un nouvel historique sera enregistré à la soumission.
                  </p>
                )}
              </Champ>
            </div>

            {/* Fiche 2 — le prêt */}
            <div className="bg-white border border-gray-100 rounded-xl p-6 space-y-5">
              <h2 className="text-sm font-semibold text-gray-800 border-b border-gray-50 pb-3">
                Détails du nouveau prêt
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <Champ label="Type de crédit" required>
                  <select value={pret.type_credit}
                    onChange={(e) => majPret("type_credit", e.target.value)}
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
                  <input type="number" min="0" value={pret.montant_sollicite}
                    onChange={(e) => majPret("montant_sollicite", e.target.value)}
                    placeholder="0"
                    className={inputClass} />
                </Champ>
                <Champ label="Durée (mois)" required>
                  <select value={pret.duree_mois}
                    onChange={(e) => majPret("duree_mois", e.target.value)}
                    className={selectClass}>
                    <option value="">Sélectionner</option>
                    {[6, 12, 18, 24, 36, 48, 60].map((m) => (
                      <option key={m} value={m}>{m} mois</option>
                    ))}
                  </select>
                </Champ>
                <Champ label="Date début prélèvement" required>
                  <input type="date" value={pret.date_debut_prelevement}
                    onChange={(e) => majPret("date_debut_prelevement", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Jour de prélèvement mensuel" required>
                  <input type="number" min="1" max="28"
                    value={pret.jour_prelevement}
                    onChange={(e) => majPret("jour_prelevement", e.target.value)}
                    placeholder="Ex : 28"
                    className={inputClass} />
                </Champ>
                <Champ label="Echéance mensuelle banque (FCFA)">
                  <input type="number" min="0" value={pret.echeance_mens_banque}
                    onChange={(e) => majPret("echeance_mens_banque", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Encours SCE (FCFA)">
                  <input type="number" min="0" value={pret.encours_sce}
                    onChange={(e) => majPret("encours_sce", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Assureur">
                  <input type="text" value={pret.assureur}
                    onChange={(e) => majPret("assureur", e.target.value)}
                    className={inputClass} />
                </Champ>
                <Champ label="Montant assurance TTC (FCFA)">
                  <input type="number" min="0" value={pret.montant_assurance_ttc}
                    onChange={(e) => majPret("montant_assurance_ttc", e.target.value)}
                    className={inputClass} />
                </Champ>
              </div>

              <Champ label="Objet du financement" required>
                <input type="text" value={pret.objet_financement}
                  onChange={(e) => majPret("objet_financement", e.target.value)}
                  placeholder="Décrire l'objet du crédit"
                  className={inputClass} />
              </Champ>

              <Champ label="Appréciation du commercial" required>
                <textarea
                  value={pret.appreciation}
                  onChange={(e) => majPret("appreciation", e.target.value)}
                  rows={4}
                  placeholder="Observations sur cette nouvelle demande..."
                  className="w-full border border-gray-200 rounded-lg px-3 py-2.5
                             text-sm text-gray-700 placeholder:text-gray-400
                             focus:outline-none focus:border-[var(--color-brand)]
                             focus:ring-2 focus:ring-[var(--color-brand)]/10 resize-none"
                />
              </Champ>

              <div className="flex items-center gap-6 pt-1">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={pret.avi}
                    onChange={(e) => majPret("avi", e.target.checked)}
                    className="w-4 h-4 accent-[var(--color-brand)]" />
                  AVI
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={pret.delegation_salaire}
                    onChange={(e) => majPret("delegation_salaire", e.target.checked)}
                    className="w-4 h-4 accent-[var(--color-brand)]" />
                  Délégation de salaire
                </label>
              </div>

              {salaireActuel > 0 && montant > 0 && (
                <div className="border-t border-gray-50 pt-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase
                                 tracking-widest mb-3">
                    Résumé financier
                  </h3>
                  <div className="grid grid-cols-4 gap-3">
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
                        valeur: necessiteComite ? "Requis" : "Non requis",
                        ok:     !necessiteComite,
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

              {erreur && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200
                              rounded px-3 py-2">
                  {erreur}
                </p>
              )}

              <button
                onClick={handleSoumettre}
                disabled={chargement}
                className="w-full h-10 rounded-lg text-sm font-medium text-white
                           disabled:opacity-50"
                style={{ background: "var(--color-brand)" }}
              >
                {chargement ? "Soumission en cours..." : "Soumettre la demande"}
              </button>
            </div>
          </div>
        )}

        {/* ── ÉTAPE RÉSULTAT ── */}
        {etape === "RESULTAT" && resultat && (
          <div className="bg-white border border-gray-100 rounded-xl p-8
                          flex flex-col items-center gap-4">
            <h2 className="text-sm font-semibold text-gray-800">
              Demande soumise — score calculé
            </h2>
            <JaugeScore score={resultat.score} niveauRisque={resultat.niveau_risque} taille={120} />
            <button
              onClick={() => router.push(`/dossiers/${resultat.dossierId}`)}
              className="h-10 px-5 rounded-lg text-sm font-medium text-white"
              style={{ background: "var(--color-brand)" }}
            >
              Voir le dossier complet
            </button>
          </div>
        )}

      </div>
    </MainLayout>
  );
}