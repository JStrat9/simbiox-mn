"use client";

import { useClientsStore } from "@/store/clients";
import { useUIStore } from "@/store/ui";
import Image from "next/image";
export function FloatingErrorsButton() {
    const clients = useClientsStore((s) => s.clients);
    const setMode = useUIStore((s) => s.setMode);
    const mode = useUIStore((s) => s.mode);

    // No mostrar en modo revisión
    if (mode === "REVIEW") return null;

    const hasErrors = Object.values(clients).some(
        (c) => c.currentErrors.length > 0
    );

    return (
        <button
            onClick={() => setMode("REVIEW")}
            className={`
                fixed bottom-4 right-4 z-50
                h-14 w-14 rounded-full shadow-lg
                flex items-center justify-center
                transition-all
                ${
                    hasErrors
                        ? "bg-red-600 text-white hover:bg-red-700"
                        : "bg-transparent border border-gray-300 shadow-lg text-gray-700"
                }
            `}
            aria-label="Ver errores de clientes"
        >
            <Image src="/chat_bubble.svg" alt="Unread chat" width={24} height={24} />
            {hasErrors && (
                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-yellow-400 text-xs flex flex-items-center justify-center pb-4">!</span>
            )}
        </button>
    );
}
