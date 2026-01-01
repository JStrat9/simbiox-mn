"use client";

import { useClientsStore } from "@/store/clients";
// components/BackToTrainingButton.tsx

import  { useUIStore } from "@/store/ui";

export function BackToTrainingButton() {
    const setMode = useUIStore((s) => s.setMode);
    const clearAllErrors = useClientsStore((s) => s.clearAllErrors);
    return (
        <button
            onClick={() => {
                setMode("TRAINING");
                clearAllErrors();
            }} 
            className="bg-zinc-900 text-white px-4 py-2 rounded-lg mb-4 hover:bg-zinc-800 transition-colors">
            Volver al entrenamiento
        </button>
    )
}