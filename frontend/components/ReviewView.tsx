"use client";

import React from "react";
import { useClientsStore } from "@/store/clients";
import { ClientCard } from "@/components/ClientCard";

const ReviewView: React.FC = () => {
    const clients = useClientsStore((s) => s.clients);

    // Convertimos Record → array con id
    const clientsArray = Object.entries(clients).map(
        ([id, client]) => ({
            id,
            ...client,
        })
    );

    const clientsWithErrors = clientsArray
        .filter((c) => c.currentErrors.length > 0)
        .sort((a, b) => b.currentErrors.length - a.currentErrors.length);

    const clientsWithoutErrors = clientsArray.filter(
        (c) => c.currentErrors.length === 0
    );

    return (
        <div className="flex min-h-screen flex-col bg-gray-100 p-4">
            {/* Header */}
            <header className="mb-4">
                <h1 className="text-2xl font-bold">Revisión técnica</h1>
                <p className="text-sm text-gray-600">
                    Clientes con incidencias durante el entreno
                </p>
            </header>

            {/* Listado */}
            <main className="flex flex-col items-center gap-2">
                {clientsWithErrors.length === 0 && (
                    <div className="rounded-xl bg-green-50 p-4 text-green-700">
                        ✅ Ningún cliente presenta errores actualmente
                    </div>
                )}

                {clientsWithErrors.map((client) => (
                    <ClientCard
                        key={client.id}
                        clientId={client.id}
                    />
                ))}

                {clientsWithoutErrors.map((client) => (
                    <ClientCard
                        key={client.id}
                        clientId={client.id}
                    />
                ))}
            </main>
        </div>
    );
};

export default ReviewView;
