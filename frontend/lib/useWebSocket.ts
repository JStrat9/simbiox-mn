"use client";

import { useEffect } from "react";
import { useAlertsStore } from "@/store/alerts";

export function useWebSocket() {
    const addAlert = useAlertsStore((state) => state.addAlert);

    useEffect(() => {
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
                        const { clientId, feedback, phase } = msg.data;
                        addAlert({
                            clientId,
                            message: `${feedback} (${phase})`,
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
