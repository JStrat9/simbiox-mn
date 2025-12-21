"use client";
// frontend/app/page.tsx

// import WSConsoleLogger from "@/components/WSConsoleLogger";
import WorkoutBoard from "@/components/WorkoutBoard";
import { AthledMinicard } from "@/components/AthledMinicard";
import { ClientCard } from "@/components/ClientCard";
import { useClientsStore } from "@/store/clients";
// import WSConsoleLogger from "@/components/WSConsoleLogger";

export default function Home() {
    const clients = useClientsStore((s) => s.clients);

    return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
            {/* <WSConsoleLogger /> */}
            <main className="flex min-h-screen w-full max-w-3xl flex-col items-center py-32 my-2 px-4 bg-white dark:bg-black sm:items-start">
                <h1 className="text-4xl font-bold">SIMBIOX</h1>
                {Object.entries(clients).map(([id]) => (
                    <ClientCard key={id} clientId={id} />
                ))}
                {/* <WorkoutBoard /> */}
                {/* <AthledMinicard /> */}
            </main>
        </div>
    );
}
