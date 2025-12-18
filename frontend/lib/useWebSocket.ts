// lib/useWebSocket.ts
"use client";

import { useEffect, useRef } from "react";
import { useAlertsStore } from "@/store/alerts";

export function useWebSocket() {
    const addAlert = useAlertsStore((state) => state.addAlert);
    const socketRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        let reconnectTimeout: NodeJS.Timeout;

        const connect = () => {
            const wsUrl = process.env.NEXT_PUBLIC_WS_URL!;
            console.log("[WS] Connecting to:", wsUrl);

            const ws = new WebSocket(wsUrl);
            socketRef.current = ws;

            ws.onopen = () => {
                console.log("[WS] Connected to WebSocket server");
            };

            ws.onmessage = (event) => {
                console.log("[WS] raw message received:", event.data);

                try {
                    const msg = JSON.parse(event.data);
                    console.log("📦 [WS] parsed message:", msg);

                    // Comprobamos que tenga el formato que enviamos
                    if (msg.type === "feedback" && msg.data) {
                        const { feedback, current_errors, reps, side, angles } =
                            msg.data;

                        // Mostrar tanto feedback acumulado como errores actuales
                        let message = "";
                        if (feedback) {
                            message = `Feedback: ${feedback}`;
                        }
                        if (current_errors && current_errors.length > 0) {
                            const errorsStr = current_errors.join(", ");
                            message +=
                                (message ? " | " : "") +
                                `Errores actuales: ${errorsStr}`;
                        }

                        message += `(Reps: ${reps}, Side: ${side})`;

                        console.log("[WS] feedback received:", message);

                        addAlert({
                            clientId: "1", // Aquí puedes mapear al cliente real si tienes varios
                            message,
                        });
                    } else {
                        console.warn("[WS] Ignored message:", msg);
                    }
                } catch (err) {
                    console.error("[WS] Failed to parse message:", err);
                }
            };

            ws.onclose = (e) => {
                console.warn(
                    "[WS] Connection closed. Reconnecting in 2s...",
                    e.reason
                );
                reconnectTimeout = setTimeout(connect, 2000);
            };

            ws.onerror = (err) => {
                console.error("[WS] WebSocket error:", err);
                ws.close();
            };
        };

        connect();

        return () => {
            clearTimeout(reconnectTimeout);
            if (
                socketRef.current &&
                socketRef.current.readyState === WebSocket.OPEN
            ) {
                socketRef.current.close();
            }
        };
    }, [addAlert]);
}
