import Image from "next/image";
import React from "react";

export function AthledMinicard() {
    return (
        <div className="flex items-center gap-3 p-3 border border-gray-200 shadow-sm rounded-lg bg-white">
            <Image
                className="rounded-full object-cover"
                alt="athled"
                src="/joan.jpg"
                width={48}
                height={48}
            />
            <div className="flex flex-col text-sm">
                <label className="text-xs text-zinc-500">Peso</label>
                <input
                    type="number"
                    className="text-lg font-semibold max-w-[60px] border-none"
                />
            </div>

            <div>
                <p className="text-xs text-zinc-500">Max Reps</p>
                <p className="font-semibold text-lg">12</p>
            </div>
        </div>
    );
}
