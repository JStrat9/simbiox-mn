"use client";

// TODO: COMPROBAR COMO HACER QUE EL BOTÓN CAMBIE DE VISTA REVIEW A WORKOUTBOARD (LIVE MODE)

import { useClientsStore } from "@/store/clients";
import { useUIStore } from "@/store/ui";

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
                        : "bg-gray-300 text-gray-700 hover:bg-gray-400"
                }
            `}
            aria-label="Ver errores de clientes"
        >
            ⚠️
            {hasErrors && (
                <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-yellow-400" />
            )}
        </button>
    );
}
