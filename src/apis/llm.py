from pathlib import Path

from apis.api import RequestMethod, request
from utils.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SUMMARY_PROMPT = (Path(__file__).parent.parent / "prompts" / "summary.md").read_text(
    "utf-8"
)


async def summarize(lines: list[str]) -> str:
    data = await request(
        RequestMethod.POST,
        f"{LLM_BASE_URL}/chat/completions",
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": "\n".join(lines)},
            ],
        },
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        timeout=120,
    )
    choice = data["choices"][0]
    text = (choice["message"].get("content") or "").strip()
    if not text or choice.get("finish_reason") == "content_filter":
        raise RuntimeError(f"LLM returned no summary: {choice.get('finish_reason')}")
    return text
