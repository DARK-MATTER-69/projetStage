"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { clientsService } from "@/services/clientsService";
import { dossiersService } from "@/services/dossiersService";
import { EtatChargement, EtatErreur } from "@/components/ui/EtatChargement";
import JaugeScore from "@/components/ui/JaugeScore";

const formaterMontant = (v: number) =>
  new Intl.NumberFormat("fr-FR").format(v) + " FCFA";

const formaterDate = (v: string) =>
  new Date(v).toLocaleDateString("fr-FR");

interface HistoriqueSalaireItem {
  id:              number;
  salaire:         number;
  date_effet:      string;
  note:            string;
  enregistre_par:  string;
}

interface ImpayeItem {
  id:                  number;
  dossier_id:          number;
  montant_impaye:      number;
  date_echeance:       string;
  statut:              string;
  statut_display:      string;
  nb_mois_retard:      number;
  date_regularisation: string | null;
}

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

const COULEURS_STATUT_IMPAYE: Record<string, string> = {
  EN_COURS:    "text-red-600 bg-red-50",
  REGULARISE:  "text-green-600 bg-green-50",
  CONTENTIEUX: "text-red-800 bg-red-100",
};

/** Formulaire d'ajout d'un nouveau salaire (déclenche le recalcul des scores) */
function FormulaireSalaire({
  clientId,
  onEnregistre,
}: {
  clientId:     number;
  onEnregistre: (message: string) => void;
}) {
  const [ouvert,      setOuvert]      = useState(false);
  const [salaire,     setSalaire]     = useState("");
  const [dateEffet,   setDateEffet]   = useState("");
  const [note,        setNote]        = useState("");
  const [chargement,  setChargement]  = useState(false);
  const [erreur,      setErreur]      = useState("");

  const handleEnregistrer = async () => {
    if (!salaire || !dateEffet) {
      setErreur("Salaire et date d'effet requis.");
      return;
    }
    setChargement(true);
    setErreur("");
    try {
      const res = await clientsService.ajouterSalaire(clientId, {
        salaire:    Number(salaire),
        date_effet: dateEffet,
        note,
      });
      onEnregistre(
        `Salaire mis à jour — ${res.scores_recalcules} score(s) recalculé(s).`
      );
      setSalaire("");
      setDateEffet("");
      setNote("");
      setOuvert(false);
    } catch {
      setErreur("Une erreur est survenue.");
    } finally {
      setChargement(false);
    }
  };

  if (!ouvert) {
    return (
      <button
        onClick={() => setOuvert(true)}
        className="text-xs font-medium px-3 py-1.5 border rounded-lg
                   transition-all hover:text-white"
        style={{ borderColor: "#922b00", color: "#922b00" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#922b00")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        + Nouveau salaire
      </button>
    );
  }

  return (
    <div className="p-4 bg-gray-50 rounded-lg space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-[10px] font-medium text-gray-400
                             uppercase tracking-wide mb-1">
            Nouveau salaire (FCFA)
          </label>
          <input type="number" min="0" value={salaire}
            onChange={(e) => setSalaire(e.target.value)}
            placeholder="0"
            className="w-full h-9 border border-gray-200 rounded-lg px-3 text-sm
                       focus:outline-none focus:border-[#922b00]" />
        </div>
        <div>
          <label className="block text-[10px] font-medium text-gray-400
                             uppercase tracking-wide mb-1">
            Date d&apos;effet
          </label>
          <input type="date" value={dateEffet}
            onChange={(e) => setDateEffet(e.target.value)}
            className="w-full h-9 border border-gray-200 rounded-lg px-3 text-sm
                       focus:outline-none focus:border-[#922b00]" />
        </div>
        <div>
          <label className="block text-[10px] font-medium text-gray-400
                             uppercase tracking-wide mb-1">
            Note
          </label>
          <input type="text" value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Ex : Promotion"
            className="w-full h-9 border border-gray-200 rounded-lg px-3 text-sm
                       focus:outline-none focus:border-[#922b00]" />
        </div>
      </div>

      {erreur && <p className="text-xs text-red-600">{erreur}</p>}

      <div className="flex gap-2">
        <button
          onClick={handleEnregistrer}
          disabled={chargement}
          className="h-8 px-3 rounded-lg text-xs font-medium text-white
                     disabled:opacity-50"
          style={{ background: "#922b00" }}
        >
          {chargement ? "Enregistrement..." : "Enregistrer et recalculer"}
        </button>
        <button
          onClick={() => setOuvert(false)}
          className="h-8 px-3 rounded-lg text-xs text-gray-500 hover:bg-gray-100"
        >
          Annuler
        </button>
      </div>
    </div>
  );
}

export default function DetailClientPage() {
  const params  = useParams();
  const router  = useRouter();
  const id      = Number(params.id);

  const [client,     setClient]     = useState<any>(null);
  const [historique, setHistorique] = useState<HistoriqueSalaireItem[]>([]);
  const [impayes,    setImpayes]    = useState<ImpayeItem[]>([]);
  const [chargement, setChargement] = useState(true);
  const [erreur,     setErreur]     = useState("");
  const [message,    setMessage]    = useState("");
  const [recalculEnCours, setRecalculEnCours] = useState<number | null>(null);

  const charger = async () => {
    try {
      const [dataClient, dataHistorique, dataImpayes] = await Promise.all([
        clientsService.detail(id),
        clientsService.historiqueSalaires(id),
        clientsService.impayes(id),
      ]);
      setClient(dataClient);
      setHistorique(dataHistorique);
      setImpayes(dataImpayes);
    } catch {
      setErreur("Client introuvable.");
    } finally {
      setChargement(false);
    }
  };

  useEffect(() => {
    if (id) charger();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleSalaireEnregistre = (msg: string) => {
    setMessage(msg);
    charger();
    setTimeout(() => setMessage(""), 5000);
  };

  const handleRegulariser = async (impayeId: number) => {
    await clientsService.regulariserImpaye(impayeId);
    charger();
  };

  const handleRecalculer = async (dossierId: number) => {
    setRecalculEnCours(dossierId);
    try {
      const res = await dossiersService.recalculer(dossierId);
      setMessage(`Dossier #${String(dossierId).padStart(5, "0")} — nouveau score : ${res.score}/100.`);
      charger();
      setTimeout(() => setMessage(""), 5000);
    } finally {
      setRecalculEnCours(null);
    }
  };

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

        {message && (
          <p className="text-sm text-green-700 bg-green-50 border border-green-200
                        rounded-lg px-4 py-2.5">
            {message}
          </p>
        )}

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
              valeur={formaterDate(client.date_naissance)} />
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
            <Info label="Salaire net actuel" valeur={formaterMontant(client.salaire_net)} />
            <Info label="Charges"         valeur={formaterMontant(client.charges_mensuelles)} />
            <Info label="Crédits en cours" valeur={formaterMontant(client.credits_en_cours)} />
            <Info label="Jour de salaire" valeur={client.date_versement_salaire || "—"} />
          </div>
        </div>

        {/* Historique des salaires */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-50 flex items-center justify-between">
            <h2 className="text-xs font-semibold text-gray-500
                           uppercase tracking-widest">
              Historique des salaires
            </h2>
            <FormulaireSalaire clientId={id} onEnregistre={handleSalaireEnregistre} />
          </div>
          <div className="divide-y divide-gray-50">
            {historique.length === 0 ? (
              <p className="px-5 py-6 text-center text-sm text-gray-400">
                Aucun historique enregistré.
              </p>
            ) : (
              historique.map((h) => (
                <div key={h.id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {formaterMontant(h.salaire)}
                    </p>
                    <p className="text-xs text-gray-400">
                      Effet le {formaterDate(h.date_effet)}
                      {h.note && ` · ${h.note}`}
                    </p>
                  </div>
                  <p className="text-xs text-gray-400">{h.enregistre_par}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Impayés SCE */}
        <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-50">
            <h2 className="text-xs font-semibold text-gray-500
                           uppercase tracking-widest">
              Impayés SCE
            </h2>
          </div>
          <div className="divide-y divide-gray-50">
            {impayes.length === 0 ? (
              <p className="px-5 py-6 text-center text-sm text-gray-400">
                Aucun impayé enregistré.
              </p>
            ) : (
              impayes.map((i) => (
                <div key={i.id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {formaterMontant(i.montant_impaye)}
                      <span className="text-xs text-gray-400 font-normal ml-2">
                        Dossier #{String(i.dossier_id).padStart(5, "0")}
                      </span>
                    </p>
                    <p className="text-xs text-gray-400">
                      Échéance {formaterDate(i.date_echeance)} · {i.nb_mois_retard} mois de retard
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium px-2 py-1 rounded-full
                                      ${COULEURS_STATUT_IMPAYE[i.statut] ?? "text-gray-600 bg-gray-50"}`}>
                      {i.statut_display}
                    </span>
                    {i.statut === "EN_COURS" && (
                      <button
                        onClick={() => handleRegulariser(i.id)}
                        className="text-xs font-medium px-2.5 py-1 border rounded-lg
                                   hover:bg-green-50 transition-colors"
                        style={{ borderColor: "#16a34a", color: "#16a34a" }}
                      >
                        Régulariser
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
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
                      {d.score !== null && d.score !== undefined && (
                        <JaugeScore score={d.score} niveauRisque={d.niveau_risque} taille={56} />
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleRecalculer(d.id)}
                      disabled={recalculEnCours === d.id}
                      className="text-xs text-gray-500 hover:text-gray-800
                                 disabled:opacity-50 transition-colors"
                    >
                      {recalculEnCours === d.id ? "Recalcul..." : "Recalculer"}
                    </button>
                    <Link
                      href={`/dossiers/${d.id}`}
                      className="text-xs hover:underline"
                      style={{ color: "#922b00" }}
                    >
                      Voir →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </MainLayout>
  );
}