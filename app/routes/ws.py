from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()
active_connections = []

@ws_router.websocket("/ws/bookings")
async def booking_ws(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_booking_update(data):
    for connection in active_connections:
        await connection.send_json(data)
