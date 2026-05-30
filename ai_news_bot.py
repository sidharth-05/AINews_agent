import requests
from datetime import datetime
import feedparser
import re
import html
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

RSS_FEEDS = [

    "https://techcrunch.com/category/artificial-intelligence/feed/",

    "https://www.theverge.com/artificial-intelligence/rss/index.xml",

    "https://hnrss.org/newest?q=ai"

]

# ---------- CLEAN TEXT ----------

def clean_text(text):

    if not text:

        return ""

    text = re.sub(r"<.*?>", "", text)

    text = html.unescape(text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

def clean_summary(text):

    text = clean_text(text)

    # strip Hacker News / RSS junk

    junk_markers = [

        "Comments URL",

        "Article URL",

        "Points:",

        "# Comments:",

        "Read more",

        "Show HN"

    ]

    for j in junk_markers:

        text = text.replace(j, "")

    return text.strip()

# ---------- FETCH ----------

def get_news():

    stories = []

    seen = set()

    for url in RSS_FEEDS:

        feed = feedparser.parse(url)

        source = feed.feed.get("title", "Unknown Source")

        for entry in feed.entries[:8]:

            title = clean_text(entry.get("title", ""))

            # hard filters to avoid junk entries

            if not title:

                continue

            if "comment" in title.lower():

                continue

            if title in seen:

                continue

            seen.add(title)

            summary = entry.get("summary", "") or entry.get("description", "")

            summary = clean_summary(summary)

            link = entry.get("link", "")

            stories.append({

                "title": title,

                "summary": summary,

                "link": link,

                "source": source

            })

    return stories

# ---------- FORMAT ----------

def format_news(stories):

    if not stories:

        return ["No news found today."]

    messages = []

    header = f"🤖 AI Daily Brief — {datetime.now().strftime('%Y-%m-%d')}\n\n"

    current = header

    for i, s in enumerate(stories[:12], 1):

        title = s["title"]

        summary = s["summary"][:220]

        source = s["source"]

        link = s["link"]

        block = f"""🧠 {i}. {title}

📌 {summary}

🏷 {source}

🔗 {link}

"""

        if len(current) + len(block) > 3500:

            messages.append(current)

            current = header + block

        else:

            current += block

    messages.append(current)

    return messages

# ---------- SEND ----------

def send(msg):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(url, data={

        "chat_id": CHAT_ID,

        "text": msg,

        "disable_web_page_preview": True

    })

    print("Telegram response:", response.status_code, response.text)

# ---------- MAIN ----------

if __name__ == "__main__":

    print("Fetching news...")

    stories = get_news()

    print(f"Fetched {len(stories)} clean stories")

    messages = format_news(stories)

    print(f"Sending {len(messages)} message(s)...")

    for msg in messages:

        send(msg)