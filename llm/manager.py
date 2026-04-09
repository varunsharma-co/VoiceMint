import os
import importlib.util
from typing import List, Optional

import config
from llm.providers.gemini_flash_2_5_lite import format_text as format_gemini_flash_2_5_lite
import utils

logger = utils.get_logger(__name__)

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def get_available_prompts() -> List[str]:
    """Returns a list of available system prompt names."""
    prompts = []
    if not os.path.exists(PROMPTS_DIR):
        return prompts
        
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith(".py") and not filename.startswith("__"):
            # e.g. "01_voice_typing.py" -> "01_voice_typing"
            prompts.append(filename[:-3])
    return sorted(prompts)

def get_prompt_text(prompt_name: str) -> Optional[str]:
    """Loads the SYSTEM_PROMPT string from the specified prompt module."""
    if not prompt_name:
        return None
        
    filepath = os.path.join(PROMPTS_DIR, f"{prompt_name}.py")
    if not os.path.exists(filepath):
        logger.warning(f"Prompt file not found: {filepath}")
        return None
        
    try:
        spec = importlib.util.spec_from_file_location(prompt_name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, "SYSTEM_PROMPT", None)
    except Exception as e:
        logger.error(f"Failed to load prompt {prompt_name}: {e}")
        
    return None

async def format_text(text: str, provider_name: str, prompt_name: str) -> str:
    """Routes the formatting request to the chosen provider."""
    system_prompt = get_prompt_text(prompt_name)
    
    if provider_name == config.LLMProvider.GEMINI_FLASH_2_5_LITE.value:
        return await format_gemini_flash_2_5_lite(text, system_prompt)
    else:
        logger.warning(f"Unknown LLM provider: {provider_name}, defaulting to Gemini")
        return await format_gemini_flash_2_5_lite(text, system_prompt)
