#!/usr/bin/env python3
"""
Static Feed Generator — Truth Is Calling
Generates a static feed.xml file that can be hosted on GitHub Pages,
Netlify, Vercel, or any static hosting provider.

Run this daily via cron, GitHub Actions, or any scheduler.
Usage: python3 generate_static_feed.py [output_dir]
"""

import datetime
import hashlib
import os
import re
import sys
import traceback
from html import escape

import feedparser
import requests

# ─── Configuration ───────────────────────────────────────────────────────────

FEED_TITLE = "Truth Is Calling — Daily Christian Feed"
FEED_DESCRIPTION = (
    "A curated daily rotation of Christian devotionals, articles, "
    "Bible verses, and video content for the Truth Is Calling community."
)
FEED_LINK = "https://truthiscalling.com"
FEED_LANGUAGE = "en-us"
MAX_ITEMS = 20
REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; TruthIsCallingBot/1.0)"

# ─── Sources ─────────────────────────────────────────────────────────────────

SOURCES = [
    {"name": "Our Daily Bread",      "url": "https://ourdailybread.org/feed/",                                                               "category": "Devotional",  "max_items": 2},
    {"name": "WELS Daily Devotions",  "url": "https://wels.net/dev-daily/feed/",                                                              "category": "Devotional",  "max_items": 1},
    {"name": "Harvest – Greg Laurie", "url": "https://harvest.org/feed/",                                                                     "category": "Devotional",  "max_items": 2},
    {"name": "Desiring God",          "url": "https://www.desiringgod.org/blog.rss",                                                          "category": "Article",     "max_items": 2},
    {"name": "Ligonier Ministries",   "url": "https://www.ligonier.org/blog/rss.xml",                                                        "category": "Teaching",    "max_items": 2},
    {"name": "Christianity Today",    "url": "https://www.christianitytoday.com/feed/",                                                       "category": "News",        "max_items": 2},
    {"name": "Faithwire",             "url": "https://www.faithwire.com/feed/",                                                               "category": "News",        "max_items": 2},
    {"name": "Relevant Magazine",     "url": "https://relevantmagazine.com/feed/",                                                            "category": "Culture",     "max_items": 1},
    {"name": "Bible Gateway Blog",    "url": "https://www.biblegateway.com/blog/feed/",                                                       "category": "Bible Study", "max_items": 1},
    {"name": "The Bible Project",     "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVfwlh9XpX2Y_tQfjeln9QA",                  "category": "Video",       "max_items": 1},
    {"name": "Ascension Presents",    "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVdGX3N-WIJ5nUvklBTNhAw",                  "category": "Video",       "max_items": 1},
    {"name": "InspiringPhilosophy",   "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5qDet6sa6rODi7t6wfpg8g",                  "category": "Video",       "max_items": 1},
]

DAILY_VERSES = [
    ("John 3:16", "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."),
    ("Proverbs 3:5-6", "Trust in the LORD with all your heart and lean not on your own understanding; in all your ways submit to him, and he will make your paths straight."),
    ("Philippians 4:13", "I can do all this through him who gives me strength."),
    ("Romans 8:28", "And we know that in all things God works for the good of those who love him, who have been called according to his purpose."),
    ("Isaiah 41:10", "So do not fear, for I am with you; do not be dismayed, for I am your God. I will strengthen you and help you; I will uphold you with my righteous right hand."),
    ("Jeremiah 29:11", "For I know the plans I have for you, declares the LORD, plans to prosper you and not to harm you, plans to give you hope and a future."),
    ("Psalm 23:1-3", "The LORD is my shepherd, I lack nothing. He makes me lie down in green pastures, he leads me beside quiet waters, he refreshes my soul."),
    ("Matthew 11:28", "Come to me, all you who are weary and burdened, and I will give you rest."),
    ("2 Corinthians 5:17", "Therefore, if anyone is in Christ, the new creation has come: The old has gone, the new is here!"),
    ("Galatians 5:22-23", "But the fruit of the Spirit is love, joy, peace, forbearance, kindness, goodness, faithfulness, gentleness and self-discipline."),
    ("Romans 12:2", "Do not conform to the pattern of this world, but be transformed by the renewing of your mind."),
    ("Psalm 46:10", "He says, Be still, and know that I am God; I will be exalted among the nations, I will be exalted in the earth."),
    ("Joshua 1:9", "Have I not commanded you? Be strong and courageous. Do not be afraid; do not be discouraged, for the LORD your God will be with you wherever you go."),
    ("1 Peter 5:7", "Cast all your anxiety on him because he cares for you."),
    ("Hebrews 11:1", "Now faith is confidence in what we hope for and assurance about what we do not see."),
    ("Psalm 119:105", "Your word is a lamp for my feet, a light on my path."),
    ("Matthew 6:33", "But seek first his kingdom and his righteousness, and all these things will be given to you as well."),
    ("Ephesians 2:8-9", "For it is by grace you have been saved, through faith — and this is not from yourselves, it is the gift of God — not by works, so that no one can boast."),
    ("Colossians 3:23", "Whatever you do, work at it with all your heart, as working for the Lord, not for human masters."),
    ("Psalm 37:4", "Take delight in the LORD, and he will give you the desires of your heart."),
    ("1 Corinthians 10:13", "No temptation has overtaken you except what is common to mankind. And God is faithful; he will not let you be tempted beyond what you can bear."),
    ("2 Timothy 1:7", "For the Spirit God gave us does not make us timid, but gives us power, love and self-discipline."),
    ("Psalm 34:18", "The LORD is close to the brokenhearted and saves those who are crushed in spirit."),
    ("James 1:2-3", "Consider it pure joy, my brothers and sisters, whenever you face trials of many kinds, because you know that the testing of your faith produces perseverance."),
    ("Romans 15:13", "May the God of hope fill you with all joy and peace as you trust in him, so that you may overflow with hope by the power of the Holy Spirit."),
    ("Lamentations 3:22-23", "Because of the LORD's great love we are not consumed, for his compassions never fail. They are new every morning; great is your faithfulness."),
    ("Psalm 91:1-2", "Whoever dwells in the shelter of the Most High will rest in the shadow of the Almighty."),
    ("John 14:6", "Jesus answered, I am the way and the truth and the life. No one comes to the Father except through me."),
    ("Isaiah 40:31", "But those who hope in the LORD will renew their strength. They will soar on wings like eagles; they will run and not grow weary, they will walk and not be faint."),
    ("Psalm 139:14", "I praise you because I am fearfully and wonderfully made; your works are wonderful, I know that full well."),
    ("Matthew 28:19-20", "Therefore go and make disciples of all nations, baptizing them in the name of the Father and of the Son and of the Holy Spirit."),
]

VERSE_IMAGES = [
    "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80",
    "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80",
    "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800&q=80",
    "https://images.unsplash.com/photo-1455849318743-b2233052fcff?w=800&q=80",
    "https://images.unsplash.com/photo-1508963493744-76fce69379c0?w=800&q=80",
    "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800&q=80",
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80",
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def fetch(url):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.text

def extract_image(entry):
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    if hasattr(entry, "media_content") and entry.media_content:
        for mc in entry.media_content:
            if mc.get("medium") == "image" or "image" in mc.get("type", ""):
                return mc.get("url", "")
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", ""):
                return enc.get("href", enc.get("url", ""))
    for f in ("content", "summary", "description"):
        t = ""
        if f == "content" and hasattr(entry, "content") and entry.content:
            t = entry.content[0].get("value", "")
        else:
            t = getattr(entry, f, "") or ""
        if t:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', t)
            if m:
                return m.group(1)
    link = getattr(entry, "link", "")
    yt = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)", link)
    if yt:
        return f"https://img.youtube.com/vi/{yt.group(1)}/hqdefault.jpg"
    return ""

def parse_date(entry):
    for a in ("published_parsed", "updated_parsed"):
        tp = getattr(entry, a, None)
        if tp:
            try:
                return datetime.datetime(*tp[:6], tzinfo=datetime.timezone.utc)
            except:
                pass
    for a in ("published", "updated"):
        raw = getattr(entry, a, "")
        if raw:
            try:
                from dateutil import parser as dp
                return dp.parse(raw)
            except:
                pass
    return datetime.datetime.now(datetime.timezone.utc)

def clean(html):
    t = re.sub(r"<[^>]+>", "", html or "")
    return re.sub(r"\s+", " ", t).strip()[:500]

def item_xml(title, link, desc, date, img, cat, src, guid):
    ds = date.strftime("%a, %d %b %Y %H:%M:%S +0000")
    dc = ""
    if img:
        dc += f'<img src="{escape(img)}" alt="{escape(title)}" style="max-width:100%;height:auto;" /><br/>'
    dc += escape(desc)
    x = f"""    <item>
      <title>{escape(title)}</title>
      <link>{escape(link)}</link>
      <description><![CDATA[{dc}]]></description>
      <pubDate>{ds}</pubDate>
      <category>{escape(cat)}</category>
      <source url="{escape(link)}">{escape(src)}</source>
      <guid isPermaLink="false">{escape(guid)}</guid>"""
    if img:
        x += f"""
      <enclosure url="{escape(img)}" type="image/jpeg" length="0" />
      <media:thumbnail url="{escape(img)}" />
      <media:content url="{escape(img)}" medium="image" />"""
    x += "\n    </item>"
    return x

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)

    now = datetime.datetime.now(datetime.timezone.utc)
    print(f"[{now.isoformat()}] Generating feed …")

    all_items = []
    for src in SOURCES:
        try:
            raw = fetch(src["url"])
            feed = feedparser.parse(raw)
            for entry in feed.entries[:src["max_items"]]:
                title = getattr(entry, "title", "Untitled")
                link = getattr(entry, "link", "")
                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary
                elif hasattr(entry, "content") and entry.content:
                    summary = entry.content[0].get("value", "")
                all_items.append({
                    "title": f"[{src['category']}] {title}",
                    "link": link,
                    "desc": clean(summary),
                    "date": parse_date(entry),
                    "img": extract_image(entry),
                    "cat": src["category"],
                    "src": src["name"],
                    "guid": hashlib.md5(f"{src['name']}:{link}".encode()).hexdigest(),
                })
            print(f"  ✓ {src['name']}: {min(len(feed.entries), src['max_items'])} items")
        except Exception as e:
            print(f"  ✗ {src['name']}: {e}")

    # Verse of the Day
    day = now.timetuple().tm_yday
    ref, text = DAILY_VERSES[day % len(DAILY_VERSES)]
    img = VERSE_IMAGES[day % len(VERSE_IMAGES)]
    verse = {
        "title": f"Verse of the Day — {ref}",
        "link": f"https://www.biblegateway.com/passage/?search={ref.replace(' ', '+')}&version=NIV",
        "desc": text,
        "date": now.replace(hour=23, minute=59, second=59),
        "img": img,
        "cat": "Verse of the Day",
        "src": "Bible Gateway",
        "guid": hashlib.md5(f"votd:{ref}:{now:%Y-%m-%d}".encode()).hexdigest(),
    }

    all_items.sort(key=lambda x: x["date"], reverse=True)
    final = [verse] + all_items[:MAX_ITEMS - 1]

    items_xml = "\n".join(item_xml(**i) for i in final)
    build = now.strftime("%a, %d %b %Y %H:%M:%S +0000")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:media="http://search.yahoo.com/mrss/"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>{escape(FEED_TITLE)}</title>
    <link>{escape(FEED_LINK)}</link>
    <description>{escape(FEED_DESCRIPTION)}</description>
    <language>{FEED_LANGUAGE}</language>
    <lastBuildDate>{build}</lastBuildDate>
    <ttl>240</ttl>
{items_xml}
  </channel>
</rss>"""

    path = os.path.join(out_dir, "feed.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"\n✓ Feed written to {path} ({len(final)} items, {len(xml)} bytes)")

if __name__ == "__main__":
    main()
