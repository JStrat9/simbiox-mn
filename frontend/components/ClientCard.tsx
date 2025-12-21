"use client";
// components/ClientCard.tsx

// TODO: REFACTOR. REVISAR SUGERENCUA CHATGPT

import { useClientsStore } from "@/store/clients";

export function ClientCard({ clientId }: { clientId: string }) {
    const client = useClientsStore((s) => s.clients[clientId]);

    if (!client) return <div className="text-sm">Clients will be here</div>;

    const hasErrors = client.currentErrors.length > 0;

    return (
        <div className="rounded-xl border border-gray-300 p-4 w-full max-w-[360px] bg-white shadow-lg my-1">
            <h2 className="text-lg font-semibold"> Cliente {clientId}</h2>

            <div className="flex justify-between text-sm mt-2">
                {/* IZQUIERDA — ERRORES */}
                <div className="flex-1">
                    <p
                        className={`font-medium ${
                            hasErrors ? "text-red-600" : "text-green-600"
                        }`}
                    >
                        {hasErrors
                            ? "⚠️ Errores actuales"
                            : "✅ Técnica correcta"}
                    </p>

                    {hasErrors && (
                        <ul className="list-disc list-inside text-sm mt-1">
                            {client.currentErrors.map((err, i) => (
                                <li key={i}>{err}</li>
                            ))}
                        </ul>
                    )}
                </div>
                {/* DERECHA — ESTADO */}
                <div className="text-right min-w-[100px]">
                    <p>Reps: {client.reps}</p>
                    <p>Ejercicio: {client.exercise}</p>
                </div>
            </div>
        </div>
    );
}
