'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { WebSocketMessage } from '@/types';
import { WS_BASE_URL } from '@/lib/constants';

export function useWebSocket(agentType: string) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) {
      setIsConnected(false);
      return;
    }

    const ws = new WebSocket(
      `${WS_BASE_URL}/api/v1/agents/ws/stream/${agentType}?token=${encodeURIComponent(token)}`
    );
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      try {
        const msg: WebSocketMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, msg]);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
    };

    ws.onerror = () => {
      setIsConnected(false);
    };
  }, [agentType]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { messages, isConnected, connect, send, disconnect, clearMessages };
}
