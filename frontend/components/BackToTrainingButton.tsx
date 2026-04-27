"use client";

import { useWebSocket } from "@/lib/useWebSocket";
import { useClientsStore } from "@/store/clients";
// components/BackToTrainingButton.tsx

import  { useUIStore } from "@/store/ui";

export function BackToTrainingButton() {
    const { send } = useWebSocket();
    const setMode = useUIStore((s) => s.setMode);
    const clearAllErrors = useClientsStore((s) => s.clearAllErrors);
    return (
        <button
            onClick={() => {
                send({ type: "CLEAR_REVIEWED_ERRORS" });
                setMode("TRAINING");
                clearAllErrors();
            }} 
            className="bg-zinc-900 text-white px-4 py-2 rounded-lg mb-4 hover:bg-zinc-800 transition-colors">
            Volver al entrenamiento
        </button>
    )
}
