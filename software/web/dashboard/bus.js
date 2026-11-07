// WebSocket client for the hub (#19). Reconnects when the hub restarts.

export const DEFAULT_HUB = 'ws://localhost:8765';
const RETRY_MS = 1000;

export function hubUrl(search) {
  return new URLSearchParams(search).get('hub') || DEFAULT_HUB;
}

export function connectBus(url, { onMessage, onStatus }) {
  let ws = null;

  function open() {
    onStatus('connecting');
    ws = new WebSocket(url);
    ws.onopen = () => onStatus('connected');
    ws.onmessage = (e) => {
      let msg;
      try {
        msg = JSON.parse(e.data);
      } catch {
        return;
      }
      if (msg && typeof msg === 'object' && typeof msg.type === 'string') onMessage(msg);
    };
    ws.onclose = () => {
      onStatus('offline');
      setTimeout(open, RETRY_MS);
    };
  }

  open();
  return {
    send(msg) {
      if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
    },
  };
}
