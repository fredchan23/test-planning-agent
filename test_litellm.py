import os
import asyncio
from google.adk.models import LiteLlm
from google.genai import types

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def main():
    llm = LiteLlm(
        model="openai/google/gemma-4-31b-it",
        api_base="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_API_KEY"),
        extra_body={"chat_template_kwargs": {"enable_thinking":True}}
    )
    request = types.GenerateContentConfig(
        max_output_tokens=100
    )
    print("LiteLlm instantiated successfully", llm.model)

asyncio.run(main())
