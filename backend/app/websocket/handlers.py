"""
SmartRescue AI — WebSocket Route Handlers
"""

import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from app.websocket.manager import ws_manager
from app.websocket.events import WSEventType, build_ws_event
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/tracking/{case_id}/{client_id}")
async def ws_location_tracking(websocket: WebSocket, case_id: str, client_id: str):
    """Live location tracking for a specific emergency case."""
    channel = f"tracking:{case_id}"
    await ws_manager.connect(websocket, channel, client_id)

    ack = build_ws_event(WSEventType.CONNECTION_ACK, {"channel": channel, "case_id": case_id})
    await ws_manager.send_personal(channel, client_id, ack)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "location_update":
                    event = build_ws_event(WSEventType.LOCATION_UPDATE, payload, case_id=case_id, actor_id=client_id)
                    await ws_manager.broadcast(channel, event)
                elif payload.get("type") == "heartbeat":
                    await ws_manager.send_personal(channel, client_id, build_ws_event(WSEventType.HEARTBEAT, {}))
            except json.JSONDecodeError:
                await ws_manager.send_personal(channel, client_id, build_ws_event(WSEventType.ERROR, {"message": "Invalid JSON"}))
    except WebSocketDisconnect:
        await ws_manager.disconnect(channel, client_id)


@router.websocket("/ws/emergency/{case_id}/{client_id}")
async def ws_emergency_updates(websocket: WebSocket, case_id: str, client_id: str):
    """Emergency case status updates."""
    channel = f"case:{case_id}"
    await ws_manager.connect(websocket, channel, client_id)

    ack = build_ws_event(WSEventType.CONNECTION_ACK, {"channel": channel, "case_id": case_id})
    await ws_manager.send_personal(channel, client_id, ack)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "heartbeat":
                    await ws_manager.send_personal(channel, client_id, build_ws_event(WSEventType.HEARTBEAT, {}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(channel, client_id)


@router.websocket("/ws/hospital/{hospital_id}/{client_id}")
async def ws_hospital_dashboard(websocket: WebSocket, hospital_id: str, client_id: str):
    """Hospital dashboard real-time feed."""
    channel = f"hospital:{hospital_id}"
    await ws_manager.connect(websocket, channel, client_id)

    ack = build_ws_event(WSEventType.CONNECTION_ACK, {"channel": channel})
    await ws_manager.send_personal(channel, client_id, ack)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "heartbeat":
                    await ws_manager.send_personal(channel, client_id, build_ws_event(WSEventType.HEARTBEAT, {}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(channel, client_id)


@router.websocket("/ws/ambulance/{ambulance_id}/{client_id}")
async def ws_ambulance_channel(websocket: WebSocket, ambulance_id: str, client_id: str):
    """Ambulance-specific real-time channel."""
    channel = f"ambulance:{ambulance_id}"
    await ws_manager.connect(websocket, channel, client_id)

    ack = build_ws_event(WSEventType.CONNECTION_ACK, {"channel": channel})
    await ws_manager.send_personal(channel, client_id, ack)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "location_update":
                    from app.services.location_service import LocationService
                    await LocationService.update_location("ambulance", ambulance_id, payload.get("latitude", 0), payload.get("longitude", 0), payload.get("heading"), payload.get("speed"))

                    active_case = payload.get("active_case_id")
                    if active_case:
                        tracking_event = build_ws_event(WSEventType.AMBULANCE_LOCATION, {"ambulance_id": ambulance_id, "latitude": payload.get("latitude"), "longitude": payload.get("longitude"), "heading": payload.get("heading"), "speed": payload.get("speed")}, case_id=active_case)
                        await ws_manager.broadcast(f"tracking:{active_case}", tracking_event)
                        await ws_manager.broadcast(f"case:{active_case}", tracking_event)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(channel, client_id)


@router.websocket("/ws/user/{user_id}")
async def ws_user_notifications(websocket: WebSocket, user_id: str):
    """User-specific notification channel."""
    channel = f"user:{user_id}"
    await ws_manager.connect(websocket, channel, user_id)

    ack = build_ws_event(WSEventType.CONNECTION_ACK, {"channel": channel})
    await ws_manager.send_personal(channel, user_id, ack)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "heartbeat":
                    await ws_manager.send_personal(channel, user_id, build_ws_event(WSEventType.HEARTBEAT, {}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(channel, user_id)
