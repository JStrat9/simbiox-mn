import React, { useState } from "react";
import WorkoutStationCard from "./WorkoutStationCard";

const athletesBase = [
    { id: "a1", name: "Joan", avatarUrl: "/joan.jpg" },
    { id: "a2", name: "Luz", avatarUrl: "/avatars/luz.jpg" },
    { id: "a3", name: "Gabbi", avatarUrl: "/avatars/gabbi.jpg" },
    { id: "a4", name: "Sandra", avatarUrl: "/avatars/sandra.jpg" },
    { id: "a5", name: "Rocío", avatarUrl: "/avatars/rocio.jpg" },
    { id: "a6", name: "Sele", avatarUrl: "/avatars/sele.jpg" },
];

const stations = [
    "Press pecho inclinado",
    "Dips",
    "Flexiones + aperturas",
    "Press pecho",
    "Tríceps agarre supino",
    "Patada de tríceps",
];

const WorkoutBoard: React.FC = () => {
    const [rotationIndex, setRotationIndex] = useState(0);

    const nextRotation = () => {
        setRotationIndex((prev) => (prev + 1) % athletesBase.length);
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
                {stations.map((exercise, stationIndex) => {
                    const athletesForStation = athletesBase.map(
                        (athlete, index) => ({
                            ...athlete,
                            weight: getSimulatedWeight(athlete.name, exercise),
                            maxReps: getSimulatedReps(),
                            isActive:
                                index ===
                                (stationIndex + rotationIndex) %
                                    athletesBase.length,
                        })
                    );

                    return (
                        <WorkoutStationCard
                            key={exercise}
                            stationNumber={stationIndex + 1}
                            exerciseName={exercise}
                            athletes={athletesForStation}
                        />
                    );
                })}
            </div>
        </div>
    );
};

/* ---------------- Simulación realista ---------------- */

function getSimulatedWeight(name: string, exercise: string) {
    const baseWeights: Record<string, number> = {
        Joan: 3.75,
        Luz: 6.25,
        Gabbi: 2.5,
        Sandra: 3.75,
        Rocío: 5,
        Sele: 15,
    };

    const multiplier = exercise.includes("Press")
        ? 1
        : exercise.includes("Tríceps")
        ? 1.4
        : exercise.includes("Dips")
        ? 0.8
        : 1;

    return Math.round(baseWeights[name] * multiplier * 4) / 4;
}

function getSimulatedReps() {
    return Math.floor(Math.random() * 6) + 10; // 10–15 reps
}

export default WorkoutBoard;
