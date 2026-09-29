import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, identifier:str):
        print(f'[WS_MANAGER] Connecting websocket id={identifier}')
        await websocket.accept()
        self.active_connections[identifier] = websocket
        print(f'[WS_MANAGER] Connected websocket id={identifier}, total_connections={len(self.active_connections)}')

    def disconnect(self, identifier:str):
        print(f'[WS_MANAGER] Disconnecting websocket id={identifier}')
        if identifier in self.active_connections:
            del self.active_connections[identifier]
        print(f'[WS_MANAGER] Disconnected websocket id={identifier}, total_connections={len(self.active_connections)}')

    async def send_personal_message(self, message: object, identifier:str):
        if identifier not in self.active_connections:
            print(f'[WS_MANAGER] No active websocket for {identifier}')
            return
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message, default=str)
            await self.active_connections[identifier].send_text(str(message))
        except Exception as e:
            print(f'[WS_MANAGER] Error sending personal message to {identifier}:', e)

    async def broadcast(self, message: str):
        for key in list(self.active_connections.keys()):
            await self.active_connections[key].send_text(message)
    
    async def isRegister(self, base_identifier:str):
        count = 0
        for key in self.active_connections.keys():
            if key.startswith(base_identifier):
                count += 1
        if count > 1:
            return True
        return False

manager = ConnectionManager()