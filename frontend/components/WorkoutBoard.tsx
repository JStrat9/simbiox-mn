// components/WorkoutBoard.tsx

import React from "react";
import WorkoutStationCard from "./WorkoutStationCard";
import { useWebSocket } from "@/lib/useWebSocket";
import { useClientsStore } from "@/store/clients";

const ATHLETE_MAP: Record<string, { name: string; avatarUrl: string }> = {
    athlete_1: { name: "Joan", avatarUrl: "/joan.jpg" },
    athlete_2: { name: "Luz", avatarUrl: "/avatars/luz.jpg" },
    athlete_3: { name: "Gabbi", avatarUrl: "/avatars/gabbi.jpg" },
    athlete_4: { name: "Sandra", avatarUrl: "/avatars/sandra.jpg" },
    athlete_5: { name: "Rocío", avatarUrl: "/avatars/rocio.jpg" },
    athlete_6: { name: "Sele", avatarUrl: "/avatars/sele.jpg" },
};

const stationNumberFromId = (stationId: string) => {
    const match = stationId.match(/\d+/);
    return match ? Number.parseInt(match[0], 10) : NaN;
};

const formatExerciseName = (exercise: string) => {
    if (!exercise) return "Ejercicio no disponible";
    return exercise
        .split("_")
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
};

const WorkoutBoard: React.FC = () => {
    const clients = useClientsStore((s) => s.clients);
    const stations = useClientsStore((s) => s.stations);
    const sessionHydrated = useClientsStore((s) => s.sessionHydrated);
    const { send } = useWebSocket();

    const orderedStations = React.useMemo(
        () =>
            Object.entries(stations).sort(([leftId], [rightId]) => {
                const leftNumber = stationNumberFromId(leftId);
                const rightNumber = stationNumberFromId(rightId);

                if (Number.isNaN(leftNumber) && Number.isNaN(rightNumber)) {
                    return leftId.localeCompare(rightId);
                }
                if (Number.isNaN(leftNumber)) return 1;
                if (Number.isNaN(rightNumber)) return -1;
                if (leftNumber === rightNumber) {
                    return leftId.localeCompare(rightId);
                }
                return leftNumber - rightNumber;
            }),
        [stations],
    );

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

            {!sessionHydrated && (
                <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-700">
                    Esperando snapshot de sesión...
                </div>
            )}

            {sessionHydrated && orderedStations.length === 0 && (
                <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-700">
                    Sesión activa sin estaciones en el snapshot.
                </div>
            )}

            {/* Estaciones */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {orderedStations.map(([stationKey, stationState], index) => {
                    const stationNumber = stationNumberFromId(stationKey);
                    const exerciseName = formatExerciseName(
                        stationState.exercise,
                    );

                    const athletesForStation = Object.entries(clients)
                        .filter(([, client]) => client.station === stationKey)
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
                            stationNumber={
                                Number.isNaN(stationNumber)
                                    ? index + 1
                                    : stationNumber
                            }
                            exerciseName={exerciseName}
                            athletes={athletesForStation}
                        />
                    );
                })}
            </div>
        </div>
    );
};

export default WorkoutBoard;
