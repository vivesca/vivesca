from __future__ import annotations

# /// script
# dependencies = [
#     "playwright",
#     "httpx",
#     "pillow",
# ]
# ///

import asyncio
import base64
import json
import os
import sys

import httpx
from playwright.async_api import async_playwright

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


async def query_gemini(screenshot_b64, task, history):
    prompt = f"""
    You are a visual web browsing agent.
    Task: {task}
    
    Current History:
    {history}
    
    Analyze the provided screenshot and decide the next action.
    Respond with ONLY a JSON object:
    {{
        "thought": "description of what you see and why you chose this action",
        "action": "navigate | click | type | wait | done",
        "target": "URL for navigate, or element text/description for click/type",
        "text": "text to type if action is type",
        "final_answer": "the result of the task if action is done"
    }}
    """

    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"},
                    },
                ],
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            )
            if response.status_code != 200:
                print(f"DEBUG: {response.text}")
            response.raise_for_status()
        except Exception as e:
            print(f"DEBUG EXCEPTION: {e}")
            raise e
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        # Clean up markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())


async def main():
    if len(sys.argv) < 2:
        print('Usage: python browse.py "task"')
        return

    task = sys.argv[1]
    history = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        print(f"🚀 Starting Visual Task: {task}")

        for step in range(1, 11):
            print(f"\n--- Step {step} ---")
            screenshot_bytes = await page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            try:
                res = await query_gemini(screenshot_b64, task, "\n".join(history))
                print(f"Thought: {res['thought']}")
                print(f"Action: {res['action']} ({res.get('target', '')})")

                history.append(f"Step {step}: {res['thought']} -> {res['action']}")

                if res["action"] == "done":
                    print(f"\n✅ TASK COMPLETE\n{res.get('final_answer')}")
                    break
                elif res["action"] == "navigate":
                    await page.goto(res["target"])
                elif res["action"] == "click":
                    # Try to find by text or role
                    target = res["target"]
                    try:
                        await page.get_by_role("button", name=target, exact=False).click(
                            timeout=3000
                        )
                    except Exception:
                        try:
                            await page.get_by_text(target, exact=False).first.click(timeout=3000)
                        except Exception:
                            print(
                                f"⚠️ Could not click '{target}', trying to find by text coordinates..."
                            )
                            # In a more advanced version, we'd use the model's coordinates
                            pass
                elif res["action"] == "type":
                    await page.get_by_role("textbox").first.fill(res["text"])
                elif res["action"] == "wait":
                    await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Error: {e}")
                break

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
