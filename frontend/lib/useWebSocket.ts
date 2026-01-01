// lib/useWebSocket.ts
"use client";

import { useEffect, useRef } from "react";
import { useClientsStore  } from "@/store/clients";

export function useWebSocket() {
    const updateClient = useClientsStore((s) => s.updateClient);
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
                try {
                    const msg = JSON.parse(event.data);
                    console.log("📦 [WS] Received message:", msg);

                    switch (msg.type) {
                        case "REP_UPDATE": {
                            const { clientId, reps } = msg;
                            updateClient(clientId, { reps });
                            break;
                        }
                        case "POSE_ERROR": {
                            const { clientId, exercise, errorCode } = msg;
                            updateClient(clientId, (prev) => ({
                                currentErrors: [
                                    ...prev.currentErrors,
                                    `${exercise}: ${errorCode}`,
                                ],
                            }));
                            break;
                        }
                        default:
                            console.warn("[WS] Unknown message type:", msg.type);
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
    }, [updateClient]);
}
