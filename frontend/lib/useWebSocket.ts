// lib/useWebSocket.ts
"use client";

import { useEffect, useRef } from "react";
import { useClientsStore } from "@/store/clients";
import type { WSMessage, WSOutgoingMessage } from "@/lib/wsTypes";

export function useWebSocket() {
    const replaceFromSessionUpdate = useClientsStore(
        (s) => s.replaceFromSessionUpdate,
    );
    const socketRef = useRef<WebSocket | null>(null);

    const send = (data: WSOutgoingMessage) => {
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

                    console.warn("[WS] Unsupported message type:", msg.type);
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
    }, [replaceFromSessionUpdate]);

    return { send };
}
