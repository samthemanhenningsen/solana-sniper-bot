# High-Speed Solana Whale Mirror Bot
# Deploy on VPS (Railway/Fly.io/Render)
# Author: Orion for Sam

import asyncio
import json
import websockets
import requests

# === CONFIGURATION ===
WHALE_ADDRESS = "5bx3JhSVcZGpGnMWtTpaE28WghUvT0H2Unb3ZB88st1X"
YOUR_WALLET = "FLyYbJNGu3AxDL1ULsyoWiKwo5e4tcMbsXpTQguwkT5t"
BUY_AMOUNT_SOL = 0.1

# Use Solana WebSocket endpoint
WS_URL = "wss://api.mainnet-beta.solana.com"
SOLSCAN_API = "https://api.solana.fm/v0/accounts/{}/transfers?cluster=mainnet-beta"

async def track_whale():
    print("Starting high-speed trade mirror for whale 2.b...")
    seen = set()

    while True:
        try:
            r = requests.get(SOLSCAN_API.format(WHALE_ADDRESS))
            data = r.json().get("result", [])

            for tx in data:
                sig = tx.get("signature")
                token = tx.get("tokenAddress")
                action = tx.get("changeType")  # "in" or "out"

                if sig not in seen:
                    seen.add(sig)
                    if action == "in":
                        print(f"[BUY] Whale bought {token}. Mirroring...")
                        execute_buy(token)
                    elif action == "out":
                        print(f"[SELL] Whale sold {token}. Mirroring...")
                        execute_sell(token)

        except Exception as e:
            print("Error fetching whale trades:", e)

        await asyncio.sleep(2)  # Near real-time polling

# Placeholder trade functions — replace with your actual logic
def execute_buy(token):
    print(f"Executing BUY for {token}")

def execute_sell(token):
    print(f"Executing SELL for {token}")

# Run the bot
if __name__ == "__main__":
    asyncio.run(track_whale())
