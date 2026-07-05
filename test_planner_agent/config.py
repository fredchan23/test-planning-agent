import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Default values
DEFAULT_SUT_URL = "https://healthspan.assurecraft.org"
MODEL_NAME = os.environ.get("MODEL_NAME", "openai/google/gemma-4-31b-it")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
NVIDIA_API_BASE = os.environ.get("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRD_SAMPLE_PATH = os.path.join(BASE_DIR, "prd_sample.md")

