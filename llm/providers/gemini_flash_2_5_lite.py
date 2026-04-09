import os
from typing import Optional
from google import genai
from google.genai import types

import utils

logger = utils.get_logger(__name__)

async def format_text(text: str, system_prompt: Optional[str] = None) -> str:
    """
    Calls the Gemini 2.5 Flash Lite API to format text.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment.")
        return "Error: GEMINI_API_KEY is not set."

    client = genai.Client(api_key=api_key)

    try:
        kwargs = {}
        if system_prompt:
            kwargs["config"] = types.GenerateContentConfig(
                system_instruction=system_prompt,
            )

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Content(parts=[types.Part.from_text(text=text)], role="user")
            ],
            **kwargs
        )
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return f"Error: {e}"
