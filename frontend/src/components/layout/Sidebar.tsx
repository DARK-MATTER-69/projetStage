"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { useAuthStore } from "@/store/authStore";
import { LABELS_ROLES } from "@/lib/roles";

interface ItemMenu {
  label: string;
  href:  string;
  icon:  React.ReactNode;
}

/** Icône SVG générique */
const Icon = ({ d }: { d: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

/** Menus par rôle */
const MENUS: Record<string, ItemMenu[]> = {
  COMMERCIAL: [
    { label: "Tableau de bord", href: "/dashboard",     icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> },
    { label: "Mes clients",     href: "/clients",       icon: <Icon d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M12 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" /> },
    { label: "Mes dossiers",    href: "/dossiers",      icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> },
    { label: "Nouveau dossier", href: "/dossiers/nouveau", icon: <Icon d="M12 5v14M5 12h14" /> },
    { label: "Nouveau prêt",    href: "/dossiers/nouveau-pret", icon: <Icon d="M12 8v8M8 12h8"/> }, 
  ],
  CHEF_AGENCE: [
    { label: "Tableau de bord", href: "/dashboard",     icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> },
    { label: "Dossiers",        href: "/dossiers",      icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> },
    { label: "Validation",      href: "/validation",    icon: <Icon d="M20 6L9 17l-5-5" /> },
  ],
  ANALYSTE: [
    { label: "Tableau de bord", href: "/dashboard",     icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> },
    { label: "Dossiers",        href: "/dossiers",      icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> },
    { label: "Analyse",         href: "/analyse",       icon: <Icon d="M18 20V10M12 20V4M6 20v-6" /> },
  ],
  DIRECTION: [
    { label: "Tableau de bord", href: "/dashboard",     icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> },
    { label: "Dossiers",        href: "/dossiers",      icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> },
    { label: "Validation",      href: "/validation",    icon: <Icon d="M20 6L9 17l-5-5" /> },
  ],
  COMITE: [
    { label: "Tableau de bord", href: "/dashboard",     icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> },
    { label: "Dossiers",        href: "/dossiers",      icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> },
    { label: "Validation",      href: "/validation",    icon: <Icon d="M20 6L9 17l-5-5" /> },
  ],
  ADMINISTRATEUR: [
    { label: "Tableau de bord", href: "/dashboard",     icon: <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> },
    { label: "Clients",         href: "/clients",       icon: <Icon d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M12 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" /> },
    { label: "Dossiers",        href: "/dossiers",      icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /> },
    { label: "Validation",      href: "/validation",    icon: <Icon d="M20 6L9 17l-5-5" /> },
    { label: "Analyse",         href: "/analyse",       icon: <Icon d="M18 20V10M12 20V4M6 20v-6" /> },
    { label: "Utilisateurs",    href: "/admin/utilisateurs", icon: <Icon d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M8.5 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM20 8v6M23 11h-6" /> },
  ],
};

export default function Sidebar() {
  const pathname              = usePathname();
  const router                = useRouter();
  const { utilisateur, deconnexion } = useAuthStore();

  const role  = utilisateur?.role || "";
  const items = MENUS[role] || [];

  const handleDeconnexion = () => {
    deconnexion();
    router.push("/login");
  };

  return (
    <aside className="w-56 flex-shrink-0 h-screen bg-white border-r border-gray-100 flex flex-col">

      {/* Logo + nom */}
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 flex-shrink-0 overflow-hidden">
            <Image
              src="/logo-sce.png"
              alt="Logo SCE"
              width={144}
              height={144}
              className="w-full h-full object-fill"
            />
          </div>
          <div>
            <p className="text-[13px] font-semibold leading-tight"
               style={{ color: "var(--color-brand)" }}>
              SCE
            </p>
            <p className="text-[10px] text-gray-400 leading-tight">
              Dossiers de crédit
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {items.map((item) => {
          const actif = pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm
                          transition-colors
                          ${actif
                            ? "bg-[var(--color-brand)]/8 text-[var(--color-brand)] font-medium"
                            : "text-gray-500 hover:bg-gray-50 hover:text-gray-800"
                          }`}
            >
              <span className={actif ? "text-[var(--color-brand)]" : "text-gray-400"}>
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Profil + déconnexion */}
      <div className="border-t border-gray-100 px-4 py-4 space-y-3">

        {/* Infos utilisateur */}
        <Link href="/profil" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-full bg-[var(--color-brand)]/10 flex items-center
                          justify-center text-[var(--color-brand)] text-sm font-semibold flex-shrink-0">
            {utilisateur?.first_name?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-gray-800 truncate group-hover:text-[var(--color-brand)] transition-colors">
              {utilisateur?.first_name} {utilisateur?.last_name}
            </p>
            <p className="text-[10px] text-gray-400 truncate">
              {LABELS_ROLES[role] || role}
            </p>
          </div>
        </Link>

        {/* Bouton déconnexion */}
        <button
          onClick={handleDeconnexion}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md
                     text-xs text-gray-400 hover:text-red-600 hover:bg-red-50
                     transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="1.8"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Se déconnecter
        </button>

      </div>
    </aside>
  );
}