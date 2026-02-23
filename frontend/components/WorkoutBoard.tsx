// components/WorkoutBoard.tsx

import React from "react";
import WorkoutStationCard from "./WorkoutStationCard";
import { useWebSocket } from "@/lib/useWebSocket";
import { useClientsStore } from "@/store/clients";

// TODO: Estos mapeos podrían venir de session_state.py. En lugar de hardcoderalos

/* ---------------- Mapeos estáticos ---------------- */
const STATION_MAP: Record<string, string> = {
    station1: "Press pecho inclinado",
    station2: "Dips",
    station3: "Flexiones + aperturas",
    station4: "Press pecho",
    station5: "Tríceps agarre supino",
    station6: "Patada de tríceps",
};

const ATHLETE_MAP: Record<string, { name: string; avatarUrl: string }> = {
    athlete_1: { name: "Joan", avatarUrl: "/joan.jpg" },
    athlete_2: { name: "Luz", avatarUrl: "/avatars/luz.jpg" },
    athlete_3: { name: "Gabbi", avatarUrl: "/avatars/gabbi.jpg" },
    athlete_4: { name: "Sandra", avatarUrl: "/avatars/sandra.jpg" },
    athlete_5: { name: "Rocío", avatarUrl: "/avatars/rocio.jpg" },
    athlete_6: { name: "Sele", avatarUrl: "/avatars/sele.jpg" },
};

const WorkoutBoard: React.FC = () => {
    const clients = useClientsStore((s) => s.clients);
    const { send } = useWebSocket();

    const nextRotation = () => {
        send({
            type: "ROTATE_STATIONS",
        });
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <h1 className="text-4xl font-bold">CROSSBOXING</h1>
            <div className="flex items-center justify-between gap-2">
                <h2 className="text-lg font-semibold">Entreno del día</h2>
                <button
                    onClick={nextRotation}
                    className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
                >
                    Siguiente rotación
                </button>
            </div>

            {/* Estaciones */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {Object.entries(STATION_MAP).map(
                    ([stationKey, stationName]) => {
                        const athletesForStation = Object.entries(clients)
                            .filter(
                                ([_, client]) => client.station === stationKey,
                            )
                            .map(([id, client]) => {
                                const meta = ATHLETE_MAP[id];
                                return {
                                    id,
                                    name: meta?.name || "Unknown",
                                    avatarUrl: meta?.avatarUrl || "",
                                    weight: 0,
                                    maxReps: client.reps,
                                    isActive: true,
                                    currentErrors: client.currentErrors,
                                };
                            });

                        return (
                            <WorkoutStationCard
                                key={stationKey}
                                stationNumber={parseInt(
                                    stationKey.replace("station", ""),
                                    10,
                                )}
                                exerciseName={stationName}
                                athletes={athletesForStation}
                            />
                        );
                    },
                )}
            </div>
        </div>
    );
};

export default WorkoutBoard;
