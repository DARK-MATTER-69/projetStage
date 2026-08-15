"use client";

interface JaugeScoreProps {
  score:         number;   // 0 à 100
  niveauRisque:  string;   // FAIBLE | MOYEN | ELEVE | CRITIQUE
  taille?:       number;   // diamètre en pixels (défaut 96)
}

const COULEURS: Record<string, string> = {
  FAIBLE:   "#16a34a",
  MOYEN:    "#ea580c",
  ELEVE:    "#dc2626",
  CRITIQUE: "#991b1b",
};

const LABELS: Record<string, string> = {
  FAIBLE:   "Risque faible",
  MOYEN:    "Risque moyen",
  ELEVE:    "Risque élevé",
  CRITIQUE: "Risque critique",
};

/**
 * Jauge circulaire affichant un score sur 100, avec un anneau qui se
 * remplit proportionnellement, coloré selon le niveau de risque.
 */
export default function JaugeScore({ score, niveauRisque, taille = 96 }: JaugeScoreProps) {
  const rayon         = (taille - 12) / 2;
  const circonference  = 2 * Math.PI * rayon;
  const progression    = Math.max(0, Math.min(100, score));
  const decalage       = circonference - (progression / 100) * circonference;
  const couleur        = COULEURS[niveauRisque] ?? "#9ca3af";

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: taille, height: taille }}>
        <svg width={taille} height={taille} className="-rotate-90">
          {/* Piste de fond */}
          <circle
            cx={taille / 2} cy={taille / 2} r={rayon}
            fill="none" stroke="#f1f5f9" strokeWidth="8"
          />
          {/* Anneau de progression */}
          <circle
            cx={taille / 2} cy={taille / 2} r={rayon}
            fill="none" stroke={couleur} strokeWidth="8"
            strokeDasharray={circonference}
            strokeDashoffset={decalage}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-gray-800">{progression}</span>
          <span className="text-[10px] text-gray-400">/100</span>
        </div>
      </div>
      <span className="text-[11px] font-medium" style={{ color: couleur }}>
        {LABELS[niveauRisque] ?? niveauRisque}
      </span>
    </div>
  );
}