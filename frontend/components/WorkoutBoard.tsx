// components/WorkoutBoard.tsx

import React from "react";
import WorkoutStationCard from "./WorkoutStationCard";
import { getAthleteProfile } from "@/lib/athleteCatalog";
import { useWebSocket } from "@/lib/useWebSocket";
import { useClientsStore } from "@/store/clients";
import { useWeightsStore } from "@/store/weights";

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
    const rotateStations = useClientsStore((s) => s.rotateStations);
    const weights = useWeightsStore((s) => s.weights);
    const updateWeight = useWeightsStore((s) => s.updateWeight);
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
        rotateStations();
        send({ type: "ROTATE_STATIONS" });
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
                        .map(([id, client]) => {
                            const athleteProfile = getAthleteProfile(id);
                            return {
                                id,
                                name: athleteProfile.name,
                                avatarUrl: athleteProfile.avatarUrl,
                                weight: weights[id]?.[stationKey] ?? 0,
                                maxReps: client.reps,
                                isActive: client.station === stationKey,
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
                            onWeightChange={(athleteId, kg) =>
                                updateWeight(athleteId, stationKey, kg)
                            }
                        />
                    );
                })}
            </div>
        </div>
    );
};

export default WorkoutBoard;
