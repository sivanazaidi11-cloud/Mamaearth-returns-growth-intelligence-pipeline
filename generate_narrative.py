"""
Part 3 — GenAI narrative layer.

Reads only narrator/findings.json, so every business number in the prompt
comes from the verified Python analysis layer.

Set:
    GEMINI_API_KEY=your_key

Optional:
    GEMINI_MODEL=gemini-2.5-flash

Run:
    python narrator/generate_narrative.py
"""

from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_FILE = ROOT / "narrator" / "findings.json"


def main():
    try:
        from google import genai
    except ImportError:
        raise SystemExit(
            "Missing dependency. Install it with: pip install google-genai"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "GEMINI_API_KEY is not set. Set the environment variable and rerun."
        )

    findings = json.loads(FINDINGS_FILE.read_text(encoding="utf-8"))

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    prompt = f"""
You are a business analyst writing an executive summary for a Mamaearth
returns and growth intelligence project.

Use ONLY the verified findings JSON below. Do not invent, recalculate,
or introduce any numeric value that is not present in the JSON.

Write:
1. Executive summary
2. Key findings
3. Return-risk interpretation
4. Growth opportunities
5. Three practical recommendations

Keep the tone professional and concise. State monetary values in INR and
percentages clearly. Recommendations must be directly tied to the evidence.

VERIFIED FINDINGS:
{json.dumps(findings, indent=2)}
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    print("\n===== MAMAEARTH RETURNS & GROWTH NARRATIVE =====\n")
    print(response.text)


if __name__ == "__main__":
    main()
