
# High-Speed Solana Whale Mirror Bot
# Deploy on VPS (Railway/Fly.io/Render)
# Author: Orion for Sam

import asyncio
import json
import websockets
import requests

# === CONFIGURATION ===
WHALE_ADDRESS = "5bx3jhSVcZGpGnMWtTpAe28WghUvT0H2Unb3ZB8st1X"
YOUR_WALLET = "PASTE_YOUR_WALLET_HERE"
BUY_AMOUNT_SOL = 0.1

# Use Solana WebSocket endpoint
WS_URL = "wss://api.mainnet-beta.solana.com"
SOLSCAN_API = "https://api.solana.fm/v0/accounts/{}/transfers?cluster=mainnet-beta".format




async def track_whale():
    print("Starting high-speed trade mirror for whale 2.b...")
    seen = set()

    while True:
        try:
            r = requests.get(SOLSCAN_API + WHALE_ADDRESS)
            data = r.json().get("data", [])
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

def execute_buy(token):
    print(f"[EXECUTING BUY] {BUY_AMOUNT_SOL} SOL into {token} for {YOUR_WALLET}")
    # Integrate BONK Bot API here if desired

def execute_sell(token):
    print(f"[EXECUTING SELL] Liquidating {token} for {YOUR_WALLET}")
    # Integrate BONK Bot API here if desired

if __name__ == "__main__":
    asyncio.run(track_whale())
