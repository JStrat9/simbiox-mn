"use client";
// components/ClientCard.tsx

import { useClientsStore } from "@/store/clients";

export function ClientCard({ clientId }: { clientId: string }) {
    const client = useClientsStore((s) => s.clients[clientId]);

    if (!client) return <div className="text-sm">Clients will be here</div>;

    const hasErrors = client.currentErrors.length > 0;

    return (
        <div className="rounded-xl border p-4 w-[360px] bg-white shadow-sm">
            <h2 className="text-lg font-semibold"> Cliente {clientId}</h2>

            <div className="flex justify-between text-sm mt-2">
                <span>Reps: {client.reps}</span>
                <span>Ejercicio: {client.exercise}</span>

                <div className="mt-3">
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
            </div>
        </div>
    );
}
