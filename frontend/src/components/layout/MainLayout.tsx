"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { useAuthStore } from "@/store/authStore";

interface MainLayoutProps {
  children: React.ReactNode;
  titre:    string;
}

export default function MainLayout({ children, titre }: MainLayoutProps) {
  const router                          = useRouter();
  const { estConnecte, tokenEstValide } = useAuthStore();

  useEffect(() => {
    if (!estConnecte || !tokenEstValide()) {
      router.push("/login");
    }
  }, [estConnecte, tokenEstValide, router]);

  if (!estConnecte) return null;

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header titre={titre} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}