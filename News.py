import os
import requests
import feedparser
from google import genai
from datetime import datetime, timedelta

# 1️⃣ API Keys (Uses GitHub Secrets if available, otherwise uses the strings you paste here)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configure the new Google GenAI client
client = genai.Client(api_key=GEMINI_KEY)

# 2️⃣ NSE tickers
nifty50 = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK"]
nifty_midcap = [
    "AU Small Finance Bank Ltd.", "Alkem Laboratories Ltd.", "Ashok Leyland Ltd.",
    "Astral Ltd.", "Aurobindo Pharma Ltd.", "BSE Ltd.", "Bharat Forge Ltd.",
    "Bharat Heavy Electricals Ltd.", "Coforge Ltd.", "Colgate Palmolive (India) Ltd.",
    "Container Corporation of India Ltd.", "Cummins India Ltd.", "Dixon Technologies (India) Ltd.",
    "Federal Bank Ltd.", "GMR Airports Ltd.", "Godrej Properties Ltd.", "HDFC Asset Management Company Ltd.",
    "Hindustan Petroleum Corporation Ltd.", "IDFC First Bank Ltd.", "Indian Railway Catering And Tourism Corporation Ltd.",
    "Indus Towers Ltd.", "Lupin Ltd.", "MRF Ltd.", "Marico Ltd.", "Max Healthcare Institute Ltd.",
    "MphasiS Ltd.", "Muthoot Finance Ltd.", "NHPC Ltd.", "NMDC Ltd.", "Oberoi Realty Ltd.",
    "Oil India Ltd.", "One 97 Communications Ltd.", "Oracle Financial Services Software Ltd.",
    "PB Fintech Ltd.", "PI Industries Ltd.", "Page Industries Ltd.", "Persistent Systems Ltd.",
    "Petronet LNG Ltd.", "Phoenix Mills Ltd.", "Polycab India Ltd.", "Prestige Estates Projects Ltd.",
    "SBI Cards and Payment Services Ltd.", "SRF Ltd.", "Steel Authority of India Ltd.", "Supreme Industries Ltd.",
    "Torrent Power Ltd.", "Tube Investments of India Ltd.", "Vodafone Idea Ltd.", "Voltas Ltd.", "Yes Bank Ltd.",
    "Aadhar Housing Finance Ltd.", "Aarti Industries Ltd.", "Action Construction Equipment Ltd.",
    "Aditya Birla Real Estate Ltd.", "Aegis Logistics Ltd.", "Afcons Infrastructure Ltd.",
    "Affle 3i Ltd.", "Amara Raja Energy & Mobility Ltd.", "Amber Enterprises India Ltd.",
    "Anant Raj Ltd.", "Angel One Ltd.", "Aster DM Healthcare Ltd.", "Atul Ltd.", "BEML Ltd.",
    "BLS International Services Ltd.", "Bata India Ltd.", "Birlasoft Ltd.", "Brainbees Solutions Ltd.",
    "Brigade Enterprises Ltd.", "CESC Ltd.", "Castrol India Ltd.", "Central Depository Services (India) Ltd.",
    "Chambal Fertilizers & Chemicals Ltd.", "Computer Age Management Services Ltd.",
    "CreditAccess Grameen Ltd.", "Crompton Greaves Consumer Electricals Ltd.", "Cyient Ltd.",
    "Data Patterns (India) Ltd.", "Delhivery Ltd.", "Devyani International Ltd.",
    "Dr. Lal Path Labs Ltd.", "Firstsource Solutions Ltd.", "Five-Star Business Finance Ltd.",
    "Garden Reach Shipbuilders & Engineers Ltd.", "Go Digit General Insurance Ltd.",
    "Godfrey Phillips India Ltd.", "Great Eastern Shipping Co. Ltd.", "Gujarat State Petronet Ltd.",
    "HBL Engineering Ltd.", "HFCL Ltd.", "Himadri Speciality Chemical Ltd.", "Hindustan Copper Ltd.",
    "IDBI Bank Ltd.", "IFCI Ltd.", "IIFL Finance Ltd.", "IRCON International Ltd.", "ITI Ltd.",
    "Indiamart Intermesh Ltd.", "Indian Energy Exchange Ltd.", "Inox Wind Ltd.",
    "International Gemmological Institute (India) Ltd.", "Inventurus Knowledge Solutions Ltd.",
    "JBM Auto Ltd.", "Jupiter Wagons Ltd.", "Kajaria Ceramics Ltd.", "Kalpataru Projects International Ltd.",
    "Karur Vysya Bank Ltd.", "Kaynes Technology India Ltd.", "Kec International Ltd.",
    "Kfin Technologies Ltd.", "Laurus Labs Ltd.", "Mahanagar Gas Ltd.", "Manappuram Finance Ltd.",
    "Multi Commodity Exchange of India Ltd.", "NATCO Pharma Ltd.", "NBCC (India) Ltd.", "NCC Ltd.",
    "Narayana Hrudayalaya Ltd.", "Navin Fluorine International Ltd.", "Neuland Laboratories Ltd.",
    "Newgen Software Technologies Ltd.", "Nuvama Wealth Management Ltd.", "PCBL Chemical Ltd.",
    "PG Electroplast Ltd.", "PNB Housing Finance Ltd.", "PVR INOX Ltd.", "Piramal Pharma Ltd.",
    "Poonawalla Fincorp Ltd.", "RITES Ltd.", "Radico Khaitan Ltd.", "Railtel Corporation Of India Ltd.",
    "Ramkrishna Forgings Ltd.", "Redington Ltd.", "Reliance Power Ltd.", "Sagility Ltd.",
    "Shyam Metalics and Energy Ltd.", "Signatureglobal (India) Ltd.", "Sonata Software Ltd.",
    "Swan Corp Ltd.", "Tata Chemicals Ltd.", "Tata Teleservices (Maharashtra) Ltd.",
    "Tejas Networks Ltd.", "Reserve bank of India MPC", "The Ramco Cements Ltd.", "Titagarh Rail Systems Ltd.", "Trident Ltd.",
    "Triveni Turbine Ltd.", "Welspun Corp Ltd.", "Welspun Living Ltd.", "Zen Technologies Ltd.",
    "Zensar Technolgies Ltd."
]
all_stocks = nifty50 + nifty_midcap

# 3️⃣ RSS feeds
rss_feeds = [
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.livemint.com/rss/business-news",
    "https://economictimes.indiatimes.com/rssfeeds/1977021501.cms",
    "https://prod-qt-images.s3.amazonaws.com/production/bloombergquint/feed.xml",
    "https://www.bseindia.com/data/xml/corporate_announcements.xml"
]

# 4️⃣ Fetch articles
def fetch_recent_articles(feeds, days=1):
    recent_articles = []
    cutoff = datetime.now() - timedelta(days=days)
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                    if published >= cutoff:
                        recent_articles.append({
                            "title": entry.title,
                            "summary": getattr(entry, 'summary', '')
                        })
                except Exception:
                    pass
    return recent_articles

# 5️⃣ Prepare Gemini prompt
def prepare_gemini_prompt(stocks, articles):
    stock_list = "\n".join(stocks)
    articles_text = "\n\n".join([f"{a['title']}: {a['summary']}" for a in articles])
    prompt = f"""
You are a financial news summarizer.

Check only the following recent articles from credible financial news sources:

{articles_text}

Focus only on these companies:

{stock_list}

Return the most recent 10 updates that mention contracts, project wins, corporate actions like dividend, stock split, promoter stake sale or orders awarded. 

Format strictly as:

TICKER: Short, 2–3 sentence news summary. : Bullish/Bearish

➡️ Each ticker must start on a new line.
➡️ Leave a blank line between each stock update.
➡️ Do not add extra explanations or JSON, only plain text updates.
"""
    return prompt

# 6️⃣ Generate updates using the new Gemini SDK
# Changed days to 1 to reduce bulk data
articles = fetch_recent_articles(rss_feeds, days=1)

if not articles:
    final_msg = "No relevant news found in the last 24 hours."
else:
    # 💡 CRITICAL FIX: Only take the 15 most recent articles to protect free tier token limits
    articles = articles[:15]
    
    prompt = prepare_gemini_prompt(all_stocks, articles)
    
    print(f"Total articles being sent to Gemini: {len(articles)}")
    print("Sending request to Gemini...")
    
try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',  # <--- Bypasses the server traffic
            contents=prompt
        )
        
        updates = response.text.strip()
        lines = [line.strip() for line in updates.split("\n") if line.strip()]
        updates_formatted = "\n\n".join(lines)
        today = datetime.now().strftime("%d-%m-%Y")
        final_msg = f"📅 Updates for {today}\n\n{updates_formatted}"
        
except Exception as e:
        final_msg = f"❌ Gemini API Error: Please wait a moment and try again.\nDetails: {str(e)}"

# 7️⃣ Send updates to Telegram
url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
payload = {"chat_id": TG_CHAT_ID, "text": final_msg}
res = requests.post(url, data=payload)
print("Telegram Response:", res.json())
