"""Generate cyberpunk dashboard section images via Gemini Nano Banana."""
import asyncio
import base64
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa

OUT = Path("/app/frontend/public/dashboard")
OUT.mkdir(parents=True, exist_ok=True)

STYLE = (
    "dark cyberpunk aesthetic, neon lighting, rain-soaked reflections, cinematic wide-angle composition, "
    "highly detailed digital painting, no text, no watermark, no words, no letters, no logos, no UI, no captions, "
    "16:9 aspect ratio landscape, empty negative space at top-left"
)

PROMPTS = {
    "inventory.png":  f"A single ornate black metal armored crate with glowing magenta purple neon veins and biohazard skull emblem, dim smoky warehouse, {STYLE}",
    "arsenal.png":    f"An array of exotic dark futuristic firearms displayed on a rack, glowing crimson red neon rim light, gunmetal and carbon fiber, {STYLE}",
    "garage.png":     f"A sleek matte black cyberpunk supercar parked in an underground garage with cyan blue neon strip lights on the walls and floor, wet concrete reflections, {STYLE}",
    "crew.png":       f"Five hooded cyberpunk gangsters lined up in the shadows of an alley, glowing amber orange neon signs behind them, cinematic silhouettes, {STYLE}",
    "heists.png":     f"A massive circular high-tech vault door with red laser trip wires crossing in front, sparks, warning lights, dark bank interior, {STYLE}",
    "properties.png": f"A luxury cyberpunk penthouse lounge interior at night, pink and violet neon strip lighting, floor to ceiling window with distant skyline, empty leather sofas, {STYLE}",
    "businesses.png": f"Interior of a neon nightclub bar counter with glowing amber orange bottles on backlit shelves, wet marble bar, no people, {STYLE}",
    "map.png":        f"Top-down aerial view of a stylized cyberpunk city grid at night with glowing green hexagonal district outlines connecting neon skyscrapers, dark ocean around it, {STYLE}",
    "progress.png":   f"A lone hooded cyberpunk figure walking away from camera up illuminated stairs toward a glowing violet neon skyline horizon, back view, {STYLE}",
    "hero.png":       f"A wide cinematic view of a lone figure in a black hoodie with a glowing pink skull on the back, standing next to a sleek black cyberpunk supercar, facing away toward a massive neon skyline of a rain-soaked megacity at night, reflections on wet pavement, {STYLE}",
    "portrait.png":   f"Close-up portrait of a fierce female cyberpunk mercenary with sidecut hair, subtle facial tattoos, black leather jacket, magenta neon rim light on hair, dark alley background, side profile looking left, no text, cinematic",
    "featured_weapon_art.png":  f"A single high-tech black SMG submachine gun floating centered on a fully transparent-looking dark black background, side profile, dramatic crimson neon rim light, no environment, no text, cinematic product shot",
    "featured_vehicle_art.png": f"A single sleek matte black cyberpunk sports coupe car floating centered on a dark black background, three quarter front view, cyan neon underglow, no environment, no text, cinematic product shot",
    "daily_contract_art.png":   f"A hooded hacker seated in front of multiple glowing red monitor screens in a dark room, back view, red rim light, cinematic, no text visible on screens, {STYLE}",
}


async def gen_one(filename: str, prompt: str):
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(api_key=api_key, session_id=f"gen-{filename}", system_message="You generate high quality images.")
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    try:
        _text, images = await chat.send_message_multimodal_response(UserMessage(text=prompt))
        if images:
            data = base64.b64decode(images[0]["data"])
            (OUT / filename).write_bytes(data)
            print(f"OK  {filename}  ({len(data)//1024} KB)")
            return True
        print(f"NO IMG {filename}")
        return False
    except Exception as e:
        print(f"ERR {filename}: {e}")
        return False


async def main(names):
    todo = {k: v for k, v in PROMPTS.items() if not names or k in names}
    for name, prompt in todo.items():
        await gen_one(name, prompt)


if __name__ == "__main__":
    names = sys.argv[1:]
    asyncio.run(main(names))
