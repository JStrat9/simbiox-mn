// lib/useWebSocket.ts
"use client";

import { useEffect, useRef } from "react";
import { useClientsStore } from "@/store/clients";
import type { WSMessage } from "@/lib/wsTypes";

export function useWebSocket() {
    const updateClient = useClientsStore((s) => s.updateClient);
    const replaceFromSessionUpdate = useClientsStore(
        (s) => s.replaceFromSessionUpdate,
    );
    const socketRef = useRef<WebSocket | null>(null);

    const send = (data: unknown) => {
        if (
            socketRef.current &&
            socketRef.current.readyState === WebSocket.OPEN
        ) {
            socketRef.current.send(JSON.stringify(data));
            console.log("[WS] Sent message:", data);
        } else {
            console.warn("[WS] Cannot send, socket not open");
        }
    };

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
                    const msg = JSON.parse(event.data) as WSMessage;
                    console.log("📦 [WS] Received message:", msg);

                    if (msg.type === "SESSION_UPDATE") {
                        replaceFromSessionUpdate(msg);
                        return;
                    }

                    const hasSnapshot = useClientsStore.getState()
                        .lastSessionVersion !== null;

                    // During Phase 1, partial events are fallback-only.
                    if (hasSnapshot) {
                        return;
                    }

                    switch (msg.type) {
                        case "REP_UPDATE": {
                            const { clientId, reps } = msg;
                            updateClient(clientId, { reps });
                            break;
                        }
                        case "POSE_ERROR": {
                            const { clientId, exercise, errorCode } = msg;
                            const newError = `${exercise}: ${errorCode}`;
                            
                            updateClient(clientId, (prev) => {
                                if (prev.currentErrors.includes(newError)) {
                                    return {};
                                }
                                return {
                                    currentErrors: [
                                        ...prev.currentErrors,
                                        newError,
                                    ],
                                };
                            });
                            break;
                        }
                        case "STATION_UPDATED": {
                            const { assignments } = msg;

                            Object.entries(assignments).forEach(
                                ([id, station]) => {
                                    updateClient(id, { station });
                                },
                            );
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
    }, [updateClient, replaceFromSessionUpdate]);

    return { send };
}
