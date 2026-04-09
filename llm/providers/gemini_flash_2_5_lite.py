import asyncio

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()

single_prompt = "Whats the capital of India?"

system_prompt = "Answer as if you are a big Narendra Modi fan"

async def gemini_call_flash_2_5_lite(prompt: str) -> str:

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[
            types.Content(parts=[types.Part.from_text(text=prompt)], role="user")
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
    )

    return response.text


async def main():

    result = await gemini_call_flash_2_5_lite(single_prompt)
    
    print(f"API Call output is {result}")


asyncio.run(main())
