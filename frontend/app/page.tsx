"use client";
// frontend/app/page.tsx

// import WSConsoleLogger from "@/components/WSConsoleLogger";
import WorkoutBoard from "@/components/WorkoutBoard";

export default function Home() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
            {/* <WSConsoleLogger /> */}
            <main className="flex min-h-screen w-full max-w-3xl flex-col items-center py-32 my-2 px-4 bg-white dark:bg-black sm:items-start">
                <WorkoutBoard />
                {/* <AthledMinicard /> */}
            </main>
        </div>
    );
}
