#!/usr/bin/env python3
"""
Truth Is Calling – Daily Christian Content Feed Aggregator
Generates a valid RSS 2.0 feed from multiple Christian content sources.
Designed for integration with Good Barber app via RSS section.

Sources include devotionals, articles, Bible study, news, and YouTube videos.
Content rotates automatically as sources publish new material.
"""

import datetime
import hashlib
import os
import re
import time
import traceback
from html import escape

import feedparser
import requests
from flask import Flask, Response, render_template_string

app = Flask(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────

FEED_TITLE = "Truth Is Calling — Daily Christian Feed"
FEED_DESCRIPTION = (
    "A curated daily rotation of Christian devotionals, articles, "
    "Bible verses, and video content for the Truth Is Calling community."
)
FEED_LINK = "https://truthiscalling.com"
FEED_LANGUAGE = "en-us"

MAX_ITEMS = 20          # max items in final feed
CACHE_DURATION = 4 * 3600  # refresh every 4 hours

REQUEST_TIMEOUT = 12
USER_AGENT = "Mozilla/5.0 (compatible; TruthIsCallingBot/1.0; +https://truthiscalling.com)"

# ─── Content Sources ─────────────────────────────────────────────────────────

SOURCES = [
    # ── Devotionals ──────────────────────────────────────────────────────
    {
        "name": "Our Daily Bread",
        "url": "https://ourdailybread.org/feed/",
        "category": "Devotional",
        "max_items": 2,
    },
    {
        "name": "WELS Daily Devotions",
        "url": "https://wels.net/dev-daily/feed/",
        "category": "Devotional",
        "max_items": 1,
    },
    {
        "name": "Harvest – Greg Laurie",
        "url": "https://harvest.org/feed/",
        "category": "Devotional",
        "max_items": 2,
    },
    # ── Articles & Teaching ──────────────────────────────────────────────
    {
        "name": "Desiring God",
        "url": "https://www.desiringgod.org/blog.rss",
        "category": "Article",
        "max_items": 2,
    },
    {
        "name": "Ligonier Ministries",
        "url": "https://www.ligonier.org/blog/rss.xml",
        "category": "Teaching",
        "max_items": 2,
    },
    # ── News ─────────────────────────────────────────────────────────────
    {
        "name": "Christianity Today",
        "url": "https://www.christianitytoday.com/feed/",
        "category": "News",
        "max_items": 2,
    },
    {
        "name": "Faithwire",
        "url": "https://www.faithwire.com/feed/",
        "category": "News",
        "max_items": 2,
    },
    {
        "name": "Relevant Magazine",
        "url": "https://relevantmagazine.com/feed/",
        "category": "Culture",
        "max_items": 1,
    },
    # ── Bible Study ──────────────────────────────────────────────────────
    {
        "name": "Bible Gateway Blog",
        "url": "https://www.biblegateway.com/blog/feed/",
        "category": "Bible Study",
        "max_items": 1,
    },
    # ── YouTube Channels (Video) ─────────────────────────────────────────
    {
        "name": "The Bible Project",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVfwlh9XpX2Y_tQfjeln9QA",
        "category": "Video",
        "max_items": 1,
    },
    {
        "name": "Ascension Presents",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVdGX3N-WIJ5nUvklBTNhAw",
        "category": "Video",
        "max_items": 1,
    },
    {
        "name": "InspiringPhilosophy",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC5qDet6sa6rODi7t6wfpg8g",
        "category": "Video",
        "max_items": 1,
    },
]

# ─── Daily Bible Verses (rotates by day-of-year) ────────────────────────────

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

# ─── Verse-of-the-day image pool (royalty-free Bible/faith images) ───────────

VERSE_IMAGES = [
    "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80",
    "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80",
    "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800&q=80",
    "https://images.unsplash.com/photo-1455849318743-b2233052fcff?w=800&q=80",
    "https://images.unsplash.com/photo-1508963493744-76fce69379c0?w=800&q=80",
    "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800&q=80",
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80",
]

# ─── Cache ───────────────────────────────────────────────────────────────────

_cache = {"xml": None, "timestamp": 0}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fetch_url(url: str) -> str:
    """Fetch a URL with proper headers and timeout."""
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.text


def _extract_image(entry) -> str:
    """Extract the best image URL from a feed entry."""
    # media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    # media:content with image
    if hasattr(entry, "media_content") and entry.media_content:
        for mc in entry.media_content:
            if mc.get("medium") == "image" or "image" in mc.get("type", ""):
                return mc.get("url", "")
    # enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", ""):
                return enc.get("href", enc.get("url", ""))
    # HTML img in content/summary
    for field_name in ("content", "summary", "description"):
        text = ""
        if field_name == "content" and hasattr(entry, "content") and entry.content:
            text = entry.content[0].get("value", "")
        else:
            text = getattr(entry, field_name, "") or ""
        if text:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', text)
            if m:
                return m.group(1)
    # YouTube thumbnail
    link = getattr(entry, "link", "")
    yt = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)", link)
    if yt:
        return f"https://img.youtube.com/vi/{yt.group(1)}/hqdefault.jpg"
    return ""


def _parse_date(entry) -> datetime.datetime:
    """Parse publication date from a feed entry."""
    for attr in ("published_parsed", "updated_parsed"):
        tp = getattr(entry, attr, None)
        if tp:
            try:
                return datetime.datetime(*tp[:6], tzinfo=datetime.timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, "")
        if raw:
            try:
                from dateutil import parser as dp
                return dp.parse(raw)
            except Exception:
                pass
    return datetime.datetime.now(datetime.timezone.utc)


def _clean_html(raw: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def _build_item(title, link, description, pub_date, image_url, category, source, guid):
    """Build a single RSS <item> element."""
    date_str = pub_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
    desc_cdata = ""
    if image_url:
        desc_cdata += f'<img src="{escape(image_url)}" alt="{escape(title)}" style="max-width:100%;height:auto;" /><br/>'
    desc_cdata += escape(description)

    xml = f"""    <item>
      <title>{escape(title)}</title>
      <link>{escape(link)}</link>
      <description><![CDATA[{desc_cdata}]]></description>
      <pubDate>{date_str}</pubDate>
      <category>{escape(category)}</category>
      <source url="{escape(link)}">{escape(source)}</source>
      <guid isPermaLink="false">{escape(guid)}</guid>"""
    if image_url:
        xml += f"""
      <enclosure url="{escape(image_url)}" type="image/jpeg" length="0" />
      <media:thumbnail url="{escape(image_url)}" />
      <media:content url="{escape(image_url)}" medium="image" />"""
    xml += "\n    </item>"
    return xml


# ─── Feed Generation ─────────────────────────────────────────────────────────

def _fetch_source(src: dict) -> list:
    """Fetch items from one source."""
    items = []
    try:
        raw = _fetch_url(src["url"])
        feed = feedparser.parse(raw)
        for entry in feed.entries[: src["max_items"]]:
            title = getattr(entry, "title", "Untitled")
            link = getattr(entry, "link", "")
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary
            elif hasattr(entry, "content") and entry.content:
                summary = entry.content[0].get("value", "")
            desc = _clean_html(summary)
            items.append({
                "title": f"[{src['category']}] {title}",
                "link": link,
                "description": desc,
                "pub_date": _parse_date(entry),
                "image_url": _extract_image(entry),
                "category": src["category"],
                "source": src["name"],
                "guid": hashlib.md5(f"{src['name']}:{link}".encode()).hexdigest(),
            })
    except Exception as exc:
        print(f"  [WARN] {src['name']}: {exc}")
    return items


def generate_feed_xml() -> str:
    """Build the complete RSS 2.0 XML document."""
    now = datetime.datetime.now(datetime.timezone.utc)
    print(f"\n[{now.isoformat()}] Building feed …")

    all_items = []
    for src in SOURCES:
        items = _fetch_source(src)
        print(f"  {src['name']}: {len(items)} items")
        all_items.extend(items)

    # ── Verse of the Day (always first) ──────────────────────────────────
    day = now.timetuple().tm_yday
    ref, text = DAILY_VERSES[day % len(DAILY_VERSES)]
    img = VERSE_IMAGES[day % len(VERSE_IMAGES)]
    verse = {
        "title": f"Verse of the Day — {ref}",
        "link": f"https://www.biblegateway.com/passage/?search={ref.replace(' ', '+')}&version=NIV",
        "description": text,
        "pub_date": now.replace(hour=23, minute=59, second=59),
        "image_url": img,
        "category": "Verse of the Day",
        "source": "Bible Gateway",
        "guid": hashlib.md5(f"votd:{ref}:{now:%Y-%m-%d}".encode()).hexdigest(),
    }

    # Sort remaining by date descending
    all_items.sort(key=lambda x: x["pub_date"], reverse=True)
    final = [verse] + all_items[: MAX_ITEMS - 1]

    # Build XML
    items_xml = "\n".join(_build_item(**i) for i in final)
    build_date = now.strftime("%a, %d %b %Y %H:%M:%S +0000")

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
    <lastBuildDate>{build_date}</lastBuildDate>
    <ttl>240</ttl>
{items_xml}
  </channel>
</rss>"""
    print(f"  Total: {len(final)} items in feed")
    return xml


def get_cached_feed() -> str:
    """Return cached XML, regenerating when stale."""
    now = time.time()
    if _cache["xml"] is None or (now - _cache["timestamp"]) > CACHE_DURATION:
        _cache["xml"] = generate_feed_xml()
        _cache["timestamp"] = now
    return _cache["xml"]


# ─── Flask Routes ────────────────────────────────────────────────────────────

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Truth Is Calling – Daily Christian Feed</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
     color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.c{max-width:720px;padding:40px;text-align:center}
.cross{font-size:56px;margin-bottom:8px;color:#d4af37}
h1{font-size:30px;color:#d4af37;letter-spacing:2px;margin-bottom:4px}
.sub{color:#8899aa;font-size:13px;margin-bottom:28px}
p{line-height:1.7;margin-bottom:18px;font-size:15px}
.url-box{background:rgba(255,255,255,.07);border:1px solid #d4af37;border-radius:8px;
          padding:14px 20px;font-family:monospace;font-size:14px;color:#d4af37;
          word-break:break-all;margin:20px 0;cursor:pointer;position:relative}
.url-box:hover::after{content:'Click to copy';position:absolute;top:-28px;left:50%;
                       transform:translateX(-50%);background:#d4af37;color:#1a1a2e;
                       padding:3px 10px;border-radius:4px;font-size:11px}
.badge{display:inline-block;background:#d4af37;color:#1a1a2e;padding:4px 12px;
       border-radius:12px;font-size:11px;font-weight:600;margin:3px}
.badges{margin:18px 0}
a.btn{display:inline-block;background:#d4af37;color:#1a1a2e;padding:12px 30px;
      border-radius:6px;text-decoration:none;font-weight:600;margin-top:18px}
a.btn:hover{background:#c9a030}
.note{font-size:13px;color:#8899aa;margin-top:24px;line-height:1.6}
</style>
</head>
<body>
<div class="c">
  <div class="cross">✝</div>
  <h1>TRUTH IS CALLING</h1>
  <div class="sub">John 18:37 — Automated Daily Christian Content Feed</div>
  <p>This RSS feed automatically aggregates and rotates Christian content daily
     from trusted sources — devotionals, articles, Bible verses, news, and
     video teachings — so you never have to search for content manually.</p>
  <div class="badges">
    <span class="badge">Verse of the Day</span>
    <span class="badge">Devotionals</span>
    <span class="badge">Articles</span>
    <span class="badge">News</span>
    <span class="badge">Bible Study</span>
    <span class="badge">Teaching</span>
    <span class="badge">Video</span>
    <span class="badge">Culture</span>
  </div>
  <div class="url-box" id="feedurl">{{ feed_url }}/feed.xml</div>
  <p class="note">
    <strong>Good Barber setup:</strong> Go to <em>Design &amp; Structure &gt;
    Structure &gt; Sections &gt; + Add a section &gt; RSS</em>, paste the URL
    above, and drag the section to the top of your app.
  </p>
  <a href="/feed.xml" class="btn">View RSS Feed</a>
</div>
<script>
document.getElementById('feedurl').addEventListener('click',function(){
  navigator.clipboard.writeText(this.textContent.trim());
  this.style.borderColor='#4caf50';
  setTimeout(()=>this.style.borderColor='#d4af37',1500);
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    host = os.environ.get("PUBLIC_URL", "[YOUR_PUBLIC_URL]")
    return render_template_string(LANDING_HTML, feed_url=host)


@app.route("/feed.xml")
def feed():
    return Response(get_cached_feed(), mimetype="application/rss+xml; charset=utf-8")


@app.route("/feed.json")
def feed_json():
    parsed = feedparser.parse(get_cached_feed())
    return {
        "count": len(parsed.entries),
        "items": [
            {
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "published": e.get("published", ""),
                "category": e.get("category", ""),
            }
            for e in parsed.entries
        ],
    }


@app.route("/health")
def health():
    return {"status": "ok", "time": datetime.datetime.now().isoformat()}


@app.route("/refresh")
def refresh():
    """Force cache refresh."""
    _cache["xml"] = None
    _cache["timestamp"] = 0
    xml = get_cached_feed()
    parsed = feedparser.parse(xml)
    return {"status": "refreshed", "items": len(parsed.entries)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
