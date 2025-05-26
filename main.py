import asyncio
import json
import requests
from bs4 import BeautifulSoup

# === CONFIGURATION ===
WHALE_NAME = "whale 2.b"
YOUR_WALLET = "PASTE_YOUR_WALLET_HERE"
BUY_AMOUNT_SOL = 0.1
SCRAPE_URL = "https://axiom.trade/trackers"
seen = set()

async def mirror_whale_trades():
    print("🔥 Live scraping trades for whale 2.b from Axiom...")

    while True:
        try:
            response = requests.get(SCRAPE_URL, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            rows = soup.select("div[class*='LiveTrades'] table tbody tr")

            for row in rows:
                columns = row.find_all("td")
                if len(columns) < 3:
                    continue

                name = columns[0].text.strip()
                token = columns[1].text.strip()
                amount = columns[2].text.strip()

                if name.lower() == WHALE_NAME.lower():
                    sig = f"{token}-{amount}"

                    if sig not in seen:
                        seen.add(sig)
                        action = "buy" if columns[0].find("span").text.lower() == WHALE_NAME.lower() else "sell"
                        
                        print(f"[{action.upper()}] Whale {action}ed {token}. Mirroring...")

                        # Replace these with real trade functions:
                        # execute_buy(token)
                        # execute_sell(token)

        except Exception as e:
            print("Error scraping Axiom:", e)

        await asyncio.sleep(4)  # ~quarter-speed scraping

if __name__ == "__main__":
    asyncio.run(mirror_whale_trades())
