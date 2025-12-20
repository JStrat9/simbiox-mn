import React from "react";
import Image from "next/image";

type Athlete = {
    id: string;
    name: string;
    avatarUrl: string;
    weight: number;
    maxReps: number;
    isActive: boolean;
};

type WorkoutStationCardProps = {
    stationNumber: number;
    exerciseName: string;
    athletes: Athlete[];
};

const WorkoutStationCard: React.FC<WorkoutStationCardProps> = ({
    stationNumber,
    exerciseName,
    athletes,
}) => {
    return (
        <div className="w-full rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            {/* Header estación */}
            <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800">
                    Estación {stationNumber}
                </h3>
                <span className="text-sm text-gray-600">{exerciseName}</span>
            </div>

            {/* Personas */}
            <div className="space-y-2">
                {athletes.map((athlete) => (
                    <div
                        key={athlete.id}
                        className={`flex items-center justify-between rounded-lg p-2 transition
              ${
                  athlete.isActive
                      ? "bg-blue-50 ring-1 ring-blue-300"
                      : "bg-gray-50"
              }`}
                    >
                        {/* Avatar + nombre */}
                        <div className="flex items-center gap-2">
                            <Image
                                src={athlete.avatarUrl}
                                alt={athlete.name}
                                className="rounded-full object-cover"
                                width={32}
                                height={32}
                            />
                            <span className="text-sm font-medium text-gray-700">
                                {athlete.name}
                            </span>
                        </div>

                        {/* Datos */}
                        <div className="flex items-center gap-4 text-sm">
                            {/* Peso */}
                            <div className="flex items-center gap-1">
                                <span className="text-gray-500">kg</span>
                                {athlete.isActive ? (
                                    <input
                                        type="number"
                                        defaultValue={athlete.weight}
                                        className="w-14 rounded-md border border-gray-300 px-1 py-0.5 text-right focus:border-blue-500 focus:outline-none"
                                    />
                                ) : (
                                    <span className="font-medium text-gray-700">
                                        {athlete.weight}
                                    </span>
                                )}
                            </div>

                            {/* Reps */}
                            <div className="text-gray-600">
                                <span className="font-semibold text-gray-800">
                                    {athlete.maxReps}
                                </span>{" "}
                                reps
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default WorkoutStationCard;
