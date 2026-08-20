"use client";

import { useAuthStore } from "@/store/authStore";
import { LABELS_ROLES } from "@/lib/roles";
import NotificationCloche from "./NotificationCloche";

interface HeaderProps {
  titre: string;
}

export default function Header({ titre }: HeaderProps) {
  const { utilisateur } = useAuthStore();
  const role = utilisateur?.role || "";

  return (
    <header className="h-14 bg-white border-b border-gray-100 px-6
                       flex items-center justify-between flex-shrink-0">
      <h1 className="text-sm font-semibold text-gray-800 tracking-wide">
        {titre}
      </h1>

      <div className="flex items-center gap-3">
        <NotificationCloche />
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span
            className="px-2 py-1 rounded text-[11px] font-medium"
            style={{ background: "rgba(146,43,0,0.08)", color: "#922b00" }}
          >
            {LABELS_ROLES[role] || role}
          </span>
          <span>{utilisateur?.agence}</span>
        </div>
      </div>
    </header>
  );
}