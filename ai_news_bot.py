import requests
from datetime import datetime
import feedparser
import re
import html
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

RSS_FEEDS = [

    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),

    ("The Verge AI", "https://www.theverge.com/artificial-intelligence/rss/index.xml"),

    ("Hacker News AI", "https://hnrss.org/newest?q=ai"),

    ("MIT Tech Review AI", "https://www.technologyreview.com/feed/"),

    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),

    ("OpenAI Blog", "https://openai.com/blog/rss.xml"),

]

# ---------- CLEANING ----------

def clean_text(text):

    if not text:

        return ""

    text = re.sub(r"<.*?>", "", text)

    text = html.unescape(text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

def clean_summary(text):

    text = clean_text(text)

    junk = [

        "Comments URL",

        "Article URL",

        "Points:",

        "# Comments:",

        "Read more",

        "Show HN"

    ]

    for j in junk:

        text = text.replace(j, "")

    return text.strip()

# ---------- SCORING SYSTEM ----------

def score_story(source, title, summary):

    score = 0

    t = title.lower()

    # source weighting

    if "MIT" in source:

        score += 5

    elif "Ars" in source:

        score += 4

    elif "OpenAI" in source:

        score += 4

    elif "TechCrunch" in source:

        score += 3

    elif "Verge" in source:

        score += 3

    elif "Hacker News" in source:

        score += 1

    # content signals

    if "ai" in t or "artificial intelligence" in t:

        score += 2

    if len(summary) > 150:

        score += 1

    if any(x in t for x in ["openai", "gpt", "google", "meta", "microsoft"]):

        score += 2

    return score

# ---------- FETCH ----------

def get_news():

    stories = []

    seen = set()

    for source_name, url in RSS_FEEDS:

        feed = feedparser.parse(url)

        for entry in feed.entries[:6]:

            title = clean_text(entry.get("title", ""))

            if not title:

                continue

            # dedupe

            if title in seen:

                continue

            seen.add(title)

            # filter junk HN posts

            if "hacker news" in source_name.lower():

                if "comment" in title.lower():

                    continue

            summary = entry.get("summary", "") or entry.get("description", "")

            summary = clean_summary(summary)

            link = entry.get("link", "")

            stories.append({

                "title": title,

                "summary": summary,

                "link": link,

                "source": source_name,

                "score": score_story(source_name, title, summary)

            })

    # rank by importance

    stories = sorted(stories, key=lambda x: x["score"], reverse=True)

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

    print("Telegram response:", response.status_code)

# ---------- MAIN ----------

if __name__ == "__main__":

    print("Fetching curated AI news...")

    stories = get_news()

    print(f"Fetched {len(stories)} ranked stories")

    messages = format_news(stories)

    print(f"Sending {len(messages)} message(s)...")

    for msg in messages:

        send(msg)