// frontend/app/page.tsx

// import WSConsoleLogger from "@/components/WSConsoleLogger";
import { ClientCard } from "@/components/ClientCard";

export default function Home() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
            {/* <WSConsoleLogger /> */}
            <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
                <div>SIMBIOX</div>
                <ClientCard clientId="1" />
            </main>
        </div>
    );
}
