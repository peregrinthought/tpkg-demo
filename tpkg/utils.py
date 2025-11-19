# tpkg/utils.py

from dotenv import load_dotenv
import os

# Load environment variables from .env into process environment
load_dotenv()

def get_api_key():
    # Reads environment variable OPENAI_API_KEY from OS memory
    # load_dotenv() above ensures .env is loaded into the env
    return os.getenv("OPENAI_API_KEY")