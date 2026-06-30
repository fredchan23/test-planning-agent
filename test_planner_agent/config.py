import os

# Default values
DEFAULT_SUT_URL = "https://healthspan.assurecraft.org"
MODEL_NAME = "gemini-2.5-flash"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRD_SAMPLE_PATH = os.path.join(BASE_DIR, "prd_sample.md")
