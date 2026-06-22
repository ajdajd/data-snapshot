import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from data_snapshot.constants import ROOT

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


SYSTEM_PROMPT_PATH = ROOT / "notebooks/schema_discovery/prompts/ontology_system.md"
USER_PROMPT_PATH = ROOT / "notebooks/schema_discovery/prompts/ontology_user.md"
FIELD_PROFILES_PATH = ROOT / "notebooks/schema_discovery/outputs/3.0-field_profiles.csv"
MODEL = "gpt-5.5"
# MAX_OUTPUT_TOKENS = 12000
OUTPUT_JSON_PATH = ROOT / "notebooks/schema_discovery/outputs/3.1-ontology_v0.json"


def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def induce_ontology():
    system_prompt = load_prompt(SYSTEM_PROMPT_PATH)
    user_prompt = load_prompt(USER_PROMPT_PATH)
    with open(FIELD_PROFILES_PATH, "rb") as f:
        csv_base64 = (
            f"data:text/csv;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=MODEL,
        # max_output_tokens=MAX_OUTPUT_TOKENS,
        reasoning={"effort": "high"},
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                # Note: Uses OpenAI's Spreadsheet Augmentation feature which only parses the first 1000 rows
                # If input is larger, use Hosted Shell
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {
                        "type": "input_file",
                        "filename": "field_profiles.csv",
                        "file_data": csv_base64,
                    },
                ],
            },
        ],
    )

    json_data = response.model_dump_json(indent=4)
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        f.write(json_data)

    return None


if __name__ == "__main__":
    induce_ontology()
