# High-Speed Solana Whale Mirror Bot (Axiom Edition)
# Author: Orion for Sam
# Mirrors whale 2.b trades live from Axiom and copies them

import asyncio
import json
import requests

# === CONFIGURATION ===
WHALE_NAME = "whale 2.b"
YOUR_WALLET = "FLyYbJNGu3AxDL1ULsyoWiKwo5e4tcMbsXpTQguwkT5t"
BUY_AMOUNT_SOL = 0.1

# Axiom scraper endpoint (mocked for now)
AXIOM_API_URL = "https://example.com/axiom/trades/whale2b"  # Replace with real or proxy URL later

async def mirror_whale_trades():
    print("🔥 Live mirroring whale 2.b trades via Axiom...")

    seen = set()

    while True:
        try:
            response = requests.get(AXIOM_API_URL)
            trades = response.json().get("trades", [])

            for trade in trades:
                sig = trade.get("signature")
                token = trade.get("token")
                action = trade.get("action")  # "buy" or "sell"

                if sig not in seen:
                    seen.add(sig)

                    if action == "buy":
                        print(f"[BUY] Whale bought {token}. Mirroring buy...")
                        execute_buy(token)
                    elif action == "sell":
                        print(f"[SELL] Whale sold {token}. Mirroring sell...")
                        execute_sell(token)

        except Exception as e:
            print("Error fetching or processing trades:", e)

        await asyncio.sleep(2)

def execute_buy(token):
    print(f"🟢 Executing buy: {token} with {BUY_AMOUNT_SOL} SOL")
    # Insert your buy logic here (e.g., call Jupiter API or BONKbot CLI)

def execute_sell(token):
    print(f"🔴 Executing sell: {token}")
    # Insert your sell logic here (e.g., call Jupiter API or BONKbot CLI)

if __name__ == "__main__":
    asyncio.run(mirror_whale_trades())
