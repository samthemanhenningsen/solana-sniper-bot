#!/usr/bin/env python3
"""Generate photorealistic site images with open-source models (FLUX.1-schnell).

The live site ships with hand-crafted SVG illustrations so it works with zero
external dependencies. Run this script on any machine with normal internet
access to replace them with AI-generated images from an open-source model.

Two backends, pick whichever you have:

1. Pollinations (free hosted FLUX, no API key):
       python3 scripts/generate_images.py

2. Local Stable Diffusion / FLUX via ComfyUI or AUTOMATIC1111:
       python3 scripts/generate_images.py --backend a1111 --url http://127.0.0.1:7860

Outputs go to assets/ as .jpg. Then update the <img> tags in index.html to
point at the .jpg files (or keep the SVGs — both look good).
"""

import argparse
import base64
import json
import pathlib
import urllib.parse
import urllib.request

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"

STYLE = (
    "warm natural light, calming teal and sand color palette, soft focus, "
    "professional photography, no text, no watermark"
)

IMAGES = {
    "hero-photo": (
        "serene therapy and wellbeing concept, calm person breathing deeply at "
        "sunrise in a desert landscape near Mexicali, golden hour, " + STYLE
    ),
    "about-photo": (
        "warm cozy psychologist office interior, two comfortable armchairs "
        "facing each other, plants, soft morning light through a window, " + STYLE
    ),
    "office-photo": (
        "modern private therapy office exterior in a sunny Mexican border city, "
        "clean facade, desert plants, welcoming entrance, " + STYLE
    ),
    "online-photo": (
        "person having a calm online therapy video call on a laptop at home, "
        "cup of tea, plant on desk, relaxed atmosphere, " + STYLE
    ),
}


def gen_pollinations(name: str, prompt: str, width: int = 1024, height: int = 768) -> None:
    """Hosted FLUX.1-schnell (open-source model), free, no key."""
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + f"?width={width}&height={height}&model=flux&nologo=true"
    )
    out = ASSETS / f"{name}.jpg"
    print(f"  {name}: fetching …")
    with urllib.request.urlopen(url, timeout=180) as resp:
        out.write_bytes(resp.read())
    print(f"  {name}: saved -> {out}")


def gen_a1111(base_url: str, name: str, prompt: str, width: int = 1024, height: int = 768) -> None:
    """Local AUTOMATIC1111 / SD WebUI txt2img endpoint (SDXL, FLUX, etc.)."""
    payload = json.dumps(
        {
            "prompt": prompt,
            "negative_prompt": "text, watermark, logo, deformed, low quality",
            "width": width,
            "height": height,
            "steps": 28,
            "cfg_scale": 6,
        }
    ).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/sdapi/v1/txt2img",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.load(resp)
    out = ASSETS / f"{name}.jpg"
    out.write_bytes(base64.b64decode(data["images"][0]))
    print(f"  {name}: saved -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["pollinations", "a1111"], default="pollinations")
    parser.add_argument("--url", default="http://127.0.0.1:7860", help="Base URL for the a1111 backend")
    args = parser.parse_args()

    print(f"Generating {len(IMAGES)} images via {args.backend} …")
    for name, prompt in IMAGES.items():
        if args.backend == "pollinations":
            gen_pollinations(name, prompt)
        else:
            gen_a1111(args.url, name, prompt)
    print("Done. Update the <img> tags in index.html if you want to use the .jpg files.")


if __name__ == "__main__":
    main()
