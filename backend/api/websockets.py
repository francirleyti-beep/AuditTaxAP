import json
import asyncio
import logging
import os
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Redis connection URL
        self.redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0") 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        logger.info(f"WebSocket connected")

    async def stream_audit_updates(self, websocket: WebSocket, audit_id: str):
        """
        Listens to Redis channel for specific audit_id and sends to this websocket.
        """
        redis = aioredis.from_url(self.redis_url)
        pubsub = redis.pubsub()
        channel = f"audit_updates:{audit_id}"
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    await websocket.send_text(data)
                    
                    # Stop listening if completed or error
                    try:
                        parsed = json.loads(data)
                        if parsed.get("status") in ["completed", "error"]:
                            break
                    except:
                        pass
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected by client: {audit_id}")
        except Exception as e:
            logger.error(f"Redis subscription error for {audit_id}: {e}")
        finally:
            await pubsub.unsubscribe(channel)
            await redis.close()
            logger.info(f"Stopped streaming for {audit_id}")

manager = ConnectionManager()

manager = ConnectionManager()
