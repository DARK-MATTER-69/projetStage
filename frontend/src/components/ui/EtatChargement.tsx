interface EtatChargementProps {
  message?: string;
}

/**
 * Composant d'état de chargement réutilisable.
 */
export function EtatChargement({ message = "Chargement..." }: EtatChargementProps) {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="flex flex-col items-center gap-3">
        <div className="w-6 h-6 border-2 rounded-full animate-spin"
          style={{ borderColor: "var(--color-brand)", borderTopColor: "transparent" }} />
        <p className="text-sm text-gray-400">{message}</p>
      </div>
    </div>
  );
}

/**
 * Composant d'état d'erreur réutilisable.
 */
export function EtatErreur({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <p className="text-sm text-red-600 bg-red-50 border border-red-100
                      rounded-lg px-4 py-3">
          {message}
        </p>
      </div>
    </div>
  );
}

/**
 * Composant état vide réutilisable.
 */
export function EtatVide({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-20">
      <p className="text-sm text-gray-400">{message}</p>
    </div>
  );
}