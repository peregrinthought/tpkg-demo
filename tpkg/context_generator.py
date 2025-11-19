import os
from dotenv import load_dotenv
from openai import OpenAI
from tpkg.utils import get_api_key
import json
import re

# --------- CACHE SETUP ----------
CACHE_DIR = ".cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Load environment variables from .env → pulls key into OS memory
load_dotenv()

# Create API client using the loaded key
client = OpenAI(api_key=get_api_key())


# ---------------------------------------------------------
# Helper: Extract valid JSON object from LLM output
# ---------------------------------------------------------
def _extract_json(text):
    """
    LLMs sometimes return extra text around the JSON.
    This function extracts the *first valid JSON object* by:
      - Locating the first '{' and last '}'
      - Slicing that substring
      - Attempting json.loads
    """

    # Locate the boundaries of a JSON object using regex
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Model returned no JSON structure:\n{text}")

    # Slice the matched substring → reduces parse errors
    json_str = match.group(0)

    # Attempt to parse JSON (can still fail)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from model:\n{json_str}") from e


# ---------------------------------------------------------
# Helper: Path for a noun's cached JSON
# ---------------------------------------------------------
def _cache_path(noun):
    return os.path.join(CACHE_DIR, f"{noun}.json")



# ---------------------------------------------------------
# Main function: Generate the 3 contextual views
# ---------------------------------------------------------
def generate_contexts(noun, paragraph):
    """
    Generate the 3 contextual views for a noun using the LLM.

    Now includes:
      - Local cache for nouns
      - Robust JSON extraction
      - Cleaner, safer output handling
    """

    # ---------- 1. CACHE HIT ----------
    cache_file = _cache_path(noun)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    # ---------- 2. CACHE MISS → LLM CALL ----------
    prompt = f"""
    You are building a contextual knowledge graph.

    For the noun: "{noun}"
    Inside this paragraph: "{paragraph}"

    Generate exactly 3 pieces of context:
    1. Second-person context: How *you* interact with this noun.
    2. First-person internal context: What the noun experiences or does internally.
    3. Third-person situational context: What role this noun plays *in this paragraph*.

    Return JSON ONLY:
    {{
      "second_person": "...",
      "first_person": "...",
      "third_person": "..."
    }}
    """

    # Sends prompt through the OpenAI chat API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2   # lower randomness → more consistent JSON
    )

    # Raw string returned by the model
    raw = response.choices[0].message.content

    # Clean + parse JSON safely
    parsed = _extract_json(raw)

    # ---------- 3. SAVE TO CACHE ----------
    with open(cache_file, "w") as f:
        json.dump(parsed, f, indent=2)

    return parsed
