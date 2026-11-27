import asyncio
import json
import traceback
import websockets
from websockets.exceptions import ConnectionClosed

import config
import history
from llm import manager
import utils

logger = utils.get_logger(__name__)

async def handle_client(websocket):
    logger.info("LLM WebSocket connected.")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action")
                logger.info(f"Received LLM action: {action}")
                
                if action == "init":
                    logger.info("Processing init request...")
                    prompts = manager.get_available_prompts()
                    default_provider = config.DEFAULT_LLM_PROVIDER.value
                    recent_messages = history.get_recent_history(limit=1)
                    recent_message = recent_messages[0] if recent_messages else ""
                    
                    response = {
                        "action": "init_response",
                        "prompts": prompts,
                        "default_provider": default_provider,
                        "recent_message": recent_message
                    }
                    logger.info(f"Sending init_response with {len(prompts)} prompts")
                    await websocket.send(json.dumps(response))
                    
                elif action == "format":
                    text = data.get("text", "")
                    prompt_name = data.get("prompt", "")
                    provider_name = data.get("provider", config.DEFAULT_LLM_PROVIDER.value)
                    logger.info(f"Processing format request for prompt: {prompt_name}, provider: {provider_name}")
                    
                    formatted_text = await manager.format_text(text, provider_name, prompt_name)
                    logger.info("Format request completed successfully")                    
                    response = {
                        "action": "format_response",
                        "formatted_text": formatted_text
                    }
                    await websocket.send(json.dumps(response))
                else:
                    logger.warning(f"Unknown LLM action: {action}")
                    await websocket.send(json.dumps({"error": f"Unknown action: {action}"}))
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM WebSocket JSON message.")
                await websocket.send(json.dumps({"error": "Invalid JSON payload"}))
            except Exception as e:
                logger.error(f"Error handling LLM message: {e}\n{traceback.format_exc()}")
                await websocket.send(json.dumps({"error": str(e)}))
    except ConnectionClosed:
        logger.info("LLM WebSocket disconnected.")
    except Exception as e:
        logger.error(f"LLM WebSocket unexpected error: {e}")

async def run_server():
    try:
        # 6468 (M-I-N-T)
        server = await websockets.serve(handle_client, "127.0.0.1", 6468)
        logger.info("LLM WebSocket server running on ws://localhost:6468")
        
        # We need a way to stop it when app_running is cleared.
        while utils.app_running.is_set():
            await asyncio.sleep(0.5)
            
        server.close()
        await server.wait_closed()
        logger.info("LLM WebSocket server shut down.")
    except Exception as e:
        logger.error(f"LLM WebSocket server crashed: {e}")

def start_server_loop():
    """Runs the asyncio event loop in this thread."""
    asyncio.run(run_server())
