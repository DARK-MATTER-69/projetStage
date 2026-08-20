"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { notificationsService, NotificationItem } from "@/services/notificationsService";

/**
 * Cloche de notifications avec badge de compteur et menu déroulant.
 * Rafraîchit la liste toutes les 30 secondes.
 */
export default function NotificationCloche() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [ouvert, setOuvert] = useState(false);
  const conteneurRef = useRef<HTMLDivElement>(null);

  const charger = async () => {
    try {
      const data = await notificationsService.lister();
      setNotifications(data);
    } catch {
      // Silencieux — pas de blocage de l'interface si ça échoue
    }
  };

  useEffect(() => {
    charger();
    const intervalle = setInterval(charger, 30000);
    return () => clearInterval(intervalle);
  }, []);

  useEffect(() => {
    const fermerSiExterieur = (e: MouseEvent) => {
      if (conteneurRef.current && !conteneurRef.current.contains(e.target as Node)) {
        setOuvert(false);
      }
    };
    document.addEventListener("mousedown", fermerSiExterieur);
    return () => document.removeEventListener("mousedown", fermerSiExterieur);
  }, []);

  const handleClicNotification = async (notif: NotificationItem) => {
    await notificationsService.marquerLue(notif.id);
    setNotifications((prev) => prev.filter((n) => n.id !== notif.id));
    setOuvert(false);
    if (notif.dossier_id) {
      router.push(`/dossiers/${notif.dossier_id}`);
    }
  };

  return (
    <div className="relative" ref={conteneurRef}>
      <button
        onClick={() => setOuvert((prev) => !prev)}
        className="relative w-8 h-8 flex items-center justify-center rounded-lg
                   hover:bg-gray-50 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"
          viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
          className="text-gray-500">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        {notifications.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1
                           rounded-full bg-red-500 text-white text-[10px]
                           font-medium flex items-center justify-center">
            {notifications.length > 9 ? "9+" : notifications.length}
          </span>
        )}
      </button>

      {ouvert && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-100
                        rounded-xl shadow-lg z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50">
            <p className="text-xs font-semibold text-gray-700">Notifications</p>
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
            {notifications.length === 0 ? (
              <p className="px-4 py-6 text-center text-xs text-gray-400">
                Aucune notification.
              </p>
            ) : (
              notifications.map((notif) => (
                <button
                  key={notif.id}
                  onClick={() => handleClicNotification(notif)}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50
                             transition-colors"
                >
                  <p className="text-xs text-gray-700">{notif.message}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    {new Date(notif.cree_le).toLocaleString("fr-FR")}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}