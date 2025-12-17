// lib/useWebSocket.ts

"use client";

import { useEffect } from "react";
import { useAlertsStore } from "@/store/alerts";

export function useWebSocket() {
    console.log("[WS HOOK] render");

    const addAlert = useAlertsStore((state) => state.addAlert);

    useEffect(() => {
        console.log("[WS HOOK] effect mounted");
        let socket: WebSocket;
        const connect = () => {
            socket = new WebSocket(process.env.NEXT_PUBLIC_WS_URL!);

            socket.onopen = () => {
                console.log("Connected to WebSocket server");
            };

            socket.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);

                    if (msg.type === "feedback" && msg.data) {
                        const { feedback, reps, side, angles } = msg.data;
                        const clientId = "1"; // Add real client ID
                        const message = `${feedback} (Reps: ${reps}, Side: ${side}, Angles: ${angles})`;
                        addAlert({
                            clientId,
                            message,
                        });
                    } else {
                        console.warn("Mensaje ws ingorado", msg);
                    }
                } catch (err) {
                    console.error("Error procesando mensaje:", err);
                }
            };

            socket.onclose = () => {
                console.log("WebSocket cerrado. Intentando reconectar...");
                setTimeout(connect, 2000);
            };
        };

        connect();

        return () => socket && socket.close();
    }, [addAlert]);
}
