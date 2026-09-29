class WebSocketsService {
    static websocket:any = null;
    static websocket_url = import.meta.env.VITE_WS_URL;
    static default_websocket_url = 'ws://localhost:5678/ws';
    static debugWs = String(import.meta.env.VITE_DEBUG_FRONT ?? 'true').toLowerCase() === 'true';
    //static websocket_url = 'ws://localhost:5678/ws'

    static log(step:string, payload:any = null){
        if (!this.debugWs) return;
        const now = new Date().toISOString();
        this.sendTraceToTerminal(step, payload);
        if (payload !== null){
            console.log(`[FRONT][${now}][WS] ${step}`, payload);
            return;
        }
        console.log(`[FRONT][${now}][WS] ${step}`);
    }

    static sendTraceToTerminal(step:string, payload:any = null){
        try {
            const tracePayload = {
                traceId: `ws-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
                step: `WS_${step}`,
                payload,
                source: 'WebSocketsService',
            };
            const text = JSON.stringify(tracePayload);
            if (navigator.sendBeacon) {
                const blob = new Blob([text], { type: 'application/json' });
                navigator.sendBeacon('/__front_trace', blob);
                return;
            }
            fetch('/__front_trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: text,
                keepalive: true,
            }).catch(() => {});
        } catch {
            // Intentionally ignore trace transport failures.
        }
    }

    static newSocket(identifier:string, setActive: (value:string) => void, setIsReportActive: (value:boolean) => void){
        let websocketUrl = this.websocket_url ?? this.default_websocket_url;
        if (typeof window !== 'undefined' && window.location.protocol === 'http:' && websocketUrl.startsWith('wss://')) {
            websocketUrl = websocketUrl.replace(/^wss:\/\//, 'ws://');
        }
        const finalUrl = `${websocketUrl}/${identifier}`;

        if (this.websocket == null) {
            this.log('CONNECTING', { websocket_url: websocketUrl, identifier, finalUrl });
            this.websocket = new WebSocket(finalUrl);
            this.websocket.onopen = () => {
                this.log('OPEN');
                console.log('Connection Started');
            };
            this.websocket.onclose = (event:any) => {
                this.log('CLOSE', {
                    code: event?.code,
                    reason: event?.reason,
                    wasClean: event?.wasClean,
                });
                console.log('Connection Closed');
            };
            this.websocket.onerror = (event:any) => {
                this.log('ERROR', event);
            };
        } else {
            this.log('CONNECT_SKIPPED_ALREADY_CONNECTED', { identifier, currentUrl: this.websocket_url });
        }

        this.websocket.onmessage = (event:any) => {
            this.log('MESSAGE_RAW', event?.data);
            let parsedMessage: any = null;
            try {
                parsedMessage = JSON.parse(event.data);
            } catch {
                parsedMessage = null;
            }

            if (parsedMessage && typeof parsedMessage === 'object') {
                this.log('MESSAGE_JSON', parsedMessage);
                if (parsedMessage.type === 'connected') {
                    setActive(parsedMessage.message || 'connected');
                    return;
                }
                if (parsedMessage.type === 'ws_log') {
                    const logText = `${parsedMessage.process}: ${parsedMessage.action}`;
                    if (parsedMessage.process === 'Role Analysis' && String(parsedMessage.action).includes('file returned')) {
                        this.log('MESSAGE_REPORT_READY_TRIGGERED');
                        setIsReportActive(true);
                    }
                    setActive(logText);
                    return;
                }
                setActive(JSON.stringify(parsedMessage));
                return;
            }

            const message = String(event.data);
            const parts = message.split(':');
            this.log('MESSAGE_PARSED', parts);
            if (parts.length > 1) {
                if (parts[0] === 'Role Analysis' && parts[1].includes('file returned')) {
                    this.log('MESSAGE_REPORT_READY_TRIGGERED');
                    setIsReportActive(true);
                }
            }
            setActive(message);
        };
    }

    static closeConnection(){
        if (this.websocket != null){
            this.log('CLOSE_REQUESTED');
            this.websocket.close();
            this.websocket = null;
            this.log('CLOSE_COMPLETED');
        }
    }
}

export default WebSocketsService;