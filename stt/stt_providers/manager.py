from typing import Optional

from config import STTProvider
from .base import BaseTranscriber, TranscriptCallback
from .soniox import SonioxTranscriber
from .assembly import AssemblyAITranscriber

def get_transcriber(provider: STTProvider, api_key: Optional[str], callback: TranscriptCallback) -> BaseTranscriber:
    """
    Factory function to get an instance of a real-time transcriber.
    """
    if not api_key:
        raise ValueError(f"API key for {provider.name} is missing or invalid.")
        
    if provider == STTProvider.SONIOX:
        return SonioxTranscriber(api_key=api_key, callback=callback)
    elif provider == STTProvider.ASSEMBLYAI:
        return AssemblyAITranscriber(api_key=api_key, callback=callback)
    
    # Deepgram is currently stubbed/not implemented for phase 1
    # elif provider == STTProvider.DEEPGRAM:
    #     return DeepgramTranscriber(api_key=api_key, callback=callback)

    raise ValueError(f"Unsupported streaming STT provider: {provider.value}")
