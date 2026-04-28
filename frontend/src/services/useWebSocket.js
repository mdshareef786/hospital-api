import { useEffect, useRef, useState, useCallback } from 'react';

export function useWebSocket(url) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      // Start ping to keep alive
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, 30000);
      ws._pingInterval = ping;
    };

    ws.onmessage = (e) => {
      if (e.data === 'pong') return;
      try {
        const msg = JSON.parse(e.data);
        if (msg.type !== 'connected') {
          setMessages((prev) => [{ ...msg, id: Date.now() }, ...prev].slice(0, 50));
        }
      } catch {}
    };

    ws.onclose = () => {
      setConnected(false);
      clearInterval(ws._pingInterval);
      // Reconnect after 3s
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const clearMessages = () => setMessages([]);

  return { messages, connected, clearMessages };
}
