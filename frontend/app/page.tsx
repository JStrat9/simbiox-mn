"use client";

import WorkoutBoard from "@/components/WorkoutBoard";
import { ClientCard } from "@/components/ClientCard";
import { FloatingErrorsButton } from "@/components/FloatingErrorsButton";
import { useClientsStore } from "@/store/clients";
import { useUIStore } from "@/store/ui";
import ReviewView from "@/components/ReviewView";

export default function Home() {
    const clients = useClientsStore((s) => s.clients);
    const mode = useUIStore((s) => s.mode);

    return (
        <div className="flex min-h-screen justify-center bg-zinc-50">
            <main className="w-full max-w-3xl px-4 py-6 bg-white">
                {mode === "TRAINING" && <WorkoutBoard />}
                {mode === "REVIEW" && <ReviewView />}

                <FloatingErrorsButton />
            </main>
        </div>
    );
}
