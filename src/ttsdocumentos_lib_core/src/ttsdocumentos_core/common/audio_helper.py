from collections.abc import AsyncGenerator
from io import BytesIO
import soundfile as sf


async def stream_audio_chunks_to_wav(chunks: AsyncGenerator, samplerate: int = 24000) -> AsyncGenerator[bytes, None]:
    """
    Recebe chunks de áudio (numpy arrays) e faz streaming em WAV usando um buffer.
    
    Args:
        chunks (AsyncGenerator): Gerador assíncrono de chunks de áudio (numpy arrays).
        samplerate (int, opcional): Taxa de amostragem. Default 24000.
    
    Yields:
        bytes: Dados WAV gerados incrementalmente.
    """
    buffer = BytesIO()
    
    with sf.SoundFile(buffer, mode='w', samplerate=samplerate, channels=1, subtype='PCM_16', format='WAV') as f:
        async for chunk in chunks:
            f.write(chunk)
            f.flush()
            buffer.seek(0)
            yield buffer.read()
            buffer.truncate(0)
            buffer.seek(0)