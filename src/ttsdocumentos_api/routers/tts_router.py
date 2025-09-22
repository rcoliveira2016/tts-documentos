from fastapi import APIRouter, WebSocket
from fastapi.responses import StreamingResponse
from ttsdocumentos_core.log.log_maneger import LogLevels, LoggerManager, LoggerNames
from ttsdocumentos_core.services.tts_service import tts_service

logger = LoggerManager(nome=LoggerNames.Core, level=LogLevels.DEBUG)

routerTTS = APIRouter(
    prefix="/tts",
    tags=["tts"],
    responses={404: {"description": "Not found"}},
)

@routerTTS.get("/")
async def tts(text: str, voice: str = "pm_santa"):
    """Gera áudio TTS via Kokoro e envia como stream."""   
    return StreamingResponse(tts_service.audio_generator(text, voice), media_type="audio/wav")

@routerTTS.websocket("/ws")
async def websocket_tts(websocket: WebSocket):
    logger.debug("Conexão WebSocket iniciada")
    await websocket.accept()
    logger.debug("WebSocket aceito")
    try:
        text = await websocket.receive_text()
        logger.debug(f"[WS] Texto recebido: {text}")

        async for audio_chunk in tts_service.audio_generator(text, "pm_santa"):
            await websocket.send_bytes(audio_chunk)

        await websocket.close()
    except Exception as e:
        logger.error(f"Erro WebSocket: {e}")
        await websocket.close()