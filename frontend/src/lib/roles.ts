/**
 * Définition des rôles de la plateforme SCE
 * et des routes autorisées pour chaque rôle.
 */

export const ROLES = {
  COMMERCIAL:     "COMMERCIAL",
  CHEF_AGENCE:    "CHEF_AGENCE",
  ANALYSTE:       "ANALYSTE",
  DIRECTION:      "DIRECTION",
  COMITE:         "COMITE",
  ADMINISTRATEUR: "ADMINISTRATEUR",
} as const;

export type Role = keyof typeof ROLES;

/** Routes accessibles par rôle */
export const ROUTES_PAR_ROLE: Record<string, string[]> = {
  COMMERCIAL:     ["/dashboard", "/dossiers", "/clients", "/profil"],
  CHEF_AGENCE:    ["/dashboard", "/dossiers", "/validation", "/profil"],
  ANALYSTE:       ["/dashboard", "/dossiers", "/analyse", "/profil"],
  DIRECTION:      ["/dashboard", "/dossiers", "/validation", "/profil"],
  COMITE:         ["/dashboard", "/dossiers", "/validation", "/profil"],
  ADMINISTRATEUR: ["/dashboard", "/dossiers", "/clients", "/validation", "/analyse", "/admin", "/profil"],
};

/** Labels affichés dans l'interface */
export const LABELS_ROLES: Record<string, string> = {
  COMMERCIAL:     "Commercial",
  CHEF_AGENCE:    "Chef d'agence",
  ANALYSTE:       "Analyste Engagement",
  DIRECTION:      "Direction",
  COMITE:         "Comité",
  ADMINISTRATEUR: "Administrateur",
};

/**
 * Vérifie si un rôle a accès à une route donnée.
 */
export const aAcces = (role: string, route: string): boolean => {
  const routes = ROUTES_PAR_ROLE[role] || [];
  return routes.some((r) => route.startsWith(r));
};