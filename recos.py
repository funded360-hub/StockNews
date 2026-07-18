import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import requests

# Telegram bot config
TELEGRAM_BOT_TOKEN = "8361961111:AAEq-c4AwFE4ZnJ4g5b8-K51vHsyxGltRYg"  # <-- Paste your token here
TELEGRAM_CHAT_ID = "-1001544282224"

URL = "https://m.moneycontrol.com/markets/broker-recommendations/"

def fetch_moneycontrol_recos():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    
    # Selenium Manager automatically handles the driver—no path needed!
    driver = webdriver.Chrome(options=options)

    driver.get(URL)
    time.sleep(5)

    recs = []
    rows = driver.find_elements(By.CSS_SELECTOR, "li")

    for r in rows:
        text = r.text.strip()
        if "|" in text:
            parts = text.split("|")
            if len(parts) >= 2:
                stock = parts[0].strip()
                rest = parts[1].strip()
                rest_parts = rest.split()
                rec_price = rest_parts[0]  # treat as target price
                broker = " ".join(rest_parts[1:]) if len(rest_parts) > 1 else ""

                recs.append({
                    "stock": stock,
                    "action": "BUY",  # default
                    "target": rec_price,
                    "broker": broker
                })

    driver.quit()
    return recs

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def main():
    recs = fetch_moneycontrol_recos()
    today = datetime.now().strftime("%d-%m-%Y")

    if not recs:
        message = f"No broker recommendations found for {today}."
    else:
        # ✅ Only take the first 5 recommendations
        top5 = recs[:5]

        lines = []
        for r in top5:
            lines.append(f"{r['stock']} :: {r['action']} :: Target {r['target']} :: {r['broker']}")
        message = f"📊 BROKER RECOMMENDATIONS - {today}\n\n" + "\n\n".join(lines)

    send_to_telegram(message)
    print("✅ Sent top 5 recommendations to Telegram!")

if __name__ == "__main__":
    main()

