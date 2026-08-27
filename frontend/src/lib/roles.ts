/**
 * Définition des rôles de la plateforme SCE
 * et des routes autorisées pour chaque rôle.
 */

export const ROLES = {
  COMMERCIAL:              "COMMERCIAL",
  CHEF_AGENCE_COMMERCIALE: "CHEF_AGENCE_COMMERCIALE",
  CHEF_AGENCE_ANALYSE:     "CHEF_AGENCE_ANALYSE",
  ANALYSTE:                "ANALYSTE",
  DIRECTION:               "DIRECTION",
  COMITE:                  "COMITE",
  ADMINISTRATEUR:          "ADMINISTRATEUR",
} as const;

export type Role = keyof typeof ROLES;

/** Routes accessibles par rôle */
export const ROUTES_PAR_ROLE: Record<string, string[]> = {
  COMMERCIAL:              ["/dashboard", "/dossiers", "/clients", "/profil"],
  CHEF_AGENCE_COMMERCIALE: ["/dashboard", "/dossiers", "/validation", "/profil"],
  CHEF_AGENCE_ANALYSE:     ["/dashboard", "/dossiers", "/validation", "/profil"],
  ANALYSTE:                ["/dashboard", "/dossiers", "/analyse", "/profil"],
  DIRECTION:               ["/dashboard", "/dossiers", "/validation", "/profil"],
  COMITE:                  ["/dashboard", "/dossiers", "/validation", "/profil"],
  ADMINISTRATEUR:          ["/dashboard", "/dossiers", "/clients", "/validation", "/analyse", "/admin", "/profil"],
};

/** Labels affichés dans l'interface */
export const LABELS_ROLES: Record<string, string> = {
  COMMERCIAL:              "Commercial",
  CHEF_AGENCE_COMMERCIALE: "Chef d'agence commerciale",
  CHEF_AGENCE_ANALYSE:     "Chef d'agence analyse",
  ANALYSTE:                "Analyste Engagement",
  DIRECTION:               "Direction",
  COMITE:                  "Comité",
  ADMINISTRATEUR:          "Administrateur",
};


/** Couleur de badge par rôle, pour distinguer d'un coup d'œil des libellés proches
 *  (ex. « Chef d'agence commerciale » vs « Chef d'agence analyse »). */
export const COULEURS_ROLES: Record<string, string> = {
  COMMERCIAL:              "text-blue-600 bg-blue-50",
  CHEF_AGENCE_COMMERCIALE: "text-amber-600 bg-amber-50",
  CHEF_AGENCE_ANALYSE:     "text-purple-600 bg-purple-50",
  ANALYSTE:                "text-teal-600 bg-teal-50",
  DIRECTION:               "text-red-600 bg-red-50",
  COMITE:                  "text-pink-600 bg-pink-50",
  ADMINISTRATEUR:          "text-gray-700 bg-gray-100",
};


/**
 * Vérifie si un rôle a accès à une route donnée.
 */
export const aAcces = (role: string, route: string): boolean => {
  const routes = ROUTES_PAR_ROLE[role] || [];
  return routes.some((r) => route.startsWith(r));
};