#!/usr/bin/env python3
"""
Daily Christian Content Feed Generator for Good Barber Custom Article Feed
Generates a JSON file in Good Barber's Custom Article Feed format.
Aggregates content from multiple Christian sources and rotates daily.
"""

import json
import hashlib
import feedparser
import requests
import re
import os
import sys
import random
from datetime import datetime, timezone
from html import escape
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────────────────

# ─── Truth Is Calling's Own Content ────────────────────────────────────────────

TRUTH_IS_CALLING_YOUTUBE = {
    "channel_handle": "TruthisCalling",
    "shorts_url": "https://www.youtube.com/@TruthisCalling/shorts",
    "max_items": 2,  # Pull 2 random Shorts from your channel
}

# Truth Is Calling website articles — REMOVED (imagery sizes were wrong)

# Christian RSS feed sources
SOURCES = [
    # Devotionals & Daily Reading
    {
        "name": "Our Daily Bread",
        "url": "https://www.odb.org/feed/",
        "category": "Devotional",
        "max_items": 2
    },
    {
        "name": "Patheos Evangelical",
        "url": "https://www.patheos.com/blogs/evangelicalpulpit/feed/",
        "category": "Teaching",
        "max_items": 2
    },
    {
        "name": "Greg Laurie Daily Devotion",
        "url": "https://www.harvest.org/resources/gregs-blog/feed",
        "category": "Devotional",
        "max_items": 1
    },
    # News & Culture
    {
        "name": "Christianity Today",
        "url": "https://www.christianitytoday.com/feed/",
        "category": "News",
        "max_items": 2
    },
    {
        "name": "Faithwire",
        "url": "https://www.faithwire.com/feed/",
        "category": "News",
        "max_items": 2
    },
    {
        "name": "Relevant Magazine",
        "url": "https://relevantmagazine.com/feed/",
        "category": "Culture",
        "max_items": 1
    },
    # Theology & Bible Study
    {
        "name": "Church Leaders",
        "url": "https://churchleaders.com/feed",
        "category": "Leadership",
        "max_items": 1
    },
    {
        "name": "Bible Gateway Blog",
        "url": "https://www.biblegateway.com/blog/feed/",
        "category": "Bible Study",
        "max_items": 1
    },
    {
        "name": "Crosswalk",
        "url": "https://www.crosswalk.com/rss/",
        "category": "Faith & Life",
        "max_items": 2
    },
    # YouTube Channels (via RSS)
    {
        "name": "The Bible Project",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCVfwlh9XpX2Y_tQfjeln9QA",
        "category": "Video",
        "max_items": 1
    },
    {
        "name": "Christian Headlines",
        "url": "https://www.christianheadlines.com/rss/",
        "category": "News",
        "max_items": 2
    },
    {
        "name": "Theology in the Raw",
        "url": "https://feeds.libsyn.com/468498/rss",
        "category": "Podcast",
        "max_items": 1
    },
    # Word on Fire (Bishop Barron)
    {
        "name": "Word on Fire",
        "url": "https://www.wordonfire.org/feed/",
        "category": "Catholic Teaching",
        "max_items": 2
    },
    # The Land and the Book (Moody Radio)
    {
        "name": "The Land and the Book",
        "url": "https://www.omnycontent.com/d/playlist/a8cdbf10-d816-4c77-9e79-aa1c012547e1/02d05ecd-1701-49e4-9921-acaf00fb51b7/67835b49-1ea7-482b-8f6d-acaf00fb51ca/podcast.rss",
        "category": "Bible & Prophecy",
        "max_items": 1
    },
]

# Daily Bible verses with themes (rotates by day of year)
DAILY_VERSES = [
    {"verse": "John 16:37", "text": "Everyone who belongs to the truth listens to my voice.", "theme": "Truth"},
    {"verse": "Jeremiah 29:11", "text": "For I know the plans I have for you, declares the Lord, plans for welfare and not for evil, to give you a future and a hope.", "theme": "Hope"},
    {"verse": "Philippians 4:13", "text": "I can do all things through him who strengthens me.", "theme": "Strength"},
    {"verse": "Romans 8:28", "text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose.", "theme": "Purpose"},
    {"verse": "Psalm 23:1", "text": "The Lord is my shepherd; I shall not want.", "theme": "Provision"},
    {"verse": "Proverbs 3:5-6", "text": "Trust in the Lord with all your heart, and do not lean on your own understanding. In all your ways acknowledge him, and he will make straight your paths.", "theme": "Trust"},
    {"verse": "Isaiah 40:31", "text": "But they who wait for the Lord shall renew their strength; they shall mount up with wings like eagles; they shall run and not be weary; they shall walk and not faint.", "theme": "Patience"},
    {"verse": "Matthew 6:33", "text": "But seek first the kingdom of God and his righteousness, and all these things will be added to you.", "theme": "Priorities"},
    {"verse": "Joshua 1:9", "text": "Have I not commanded you? Be strong and courageous. Do not be frightened, and do not be dismayed, for the Lord your God is with you wherever you go.", "theme": "Courage"},
    {"verse": "Psalm 46:10", "text": "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth!", "theme": "Peace"},
    {"verse": "Romans 12:2", "text": "Do not be conformed to this world, but be transformed by the renewal of your mind, that by testing you may discern what is the will of God, what is good and acceptable and perfect.", "theme": "Transformation"},
    {"verse": "2 Timothy 1:7", "text": "For God gave us a spirit not of fear but of power and love and self-control.", "theme": "Power"},
    {"verse": "Hebrews 11:1", "text": "Now faith is the assurance of things hoped for, the conviction of things not seen.", "theme": "Faith"},
    {"verse": "Psalm 119:105", "text": "Your word is a lamp to my feet and a light to my path.", "theme": "Guidance"},
    {"verse": "Ephesians 2:8-9", "text": "For by grace you have been saved through faith. And this is not your own doing; it is the gift of God, not a result of works, so that no one may boast.", "theme": "Grace"},
    {"verse": "1 Corinthians 13:4-7", "text": "Love is patient and kind; love does not envy or boast; it is not arrogant or rude. It does not insist on its own way; it is not irritable or resentful.", "theme": "Love"},
    {"verse": "Galatians 5:22-23", "text": "But the fruit of the Spirit is love, joy, peace, patience, kindness, goodness, faithfulness, gentleness, self-control; against such things there is no law.", "theme": "Fruit of the Spirit"},
    {"verse": "Matthew 28:19-20", "text": "Go therefore and make disciples of all nations, baptizing them in the name of the Father and of the Son and of the Holy Spirit, teaching them to observe all that I have commanded you.", "theme": "Mission"},
    {"verse": "Psalm 37:4", "text": "Delight yourself in the Lord, and he will give you the desires of your heart.", "theme": "Delight"},
    {"verse": "Colossians 3:23", "text": "Whatever you do, work heartily, as for the Lord and not for men.", "theme": "Work"},
    {"verse": "1 Peter 5:7", "text": "Casting all your anxieties on him, because he cares for you.", "theme": "Anxiety"},
    {"verse": "James 1:2-3", "text": "Count it all joy, my brothers, when you meet trials of various kinds, for you know that the testing of your faith produces steadfastness.", "theme": "Trials"},
    {"verse": "Deuteronomy 31:6", "text": "Be strong and courageous. Do not fear or be in dread of them, for it is the Lord your God who goes with you. He will not leave you or forsake you.", "theme": "Courage"},
    {"verse": "Psalm 27:1", "text": "The Lord is my light and my salvation; whom shall I fear? The Lord is the stronghold of my life; of whom shall I be afraid?", "theme": "Fearlessness"},
    {"verse": "Isaiah 41:10", "text": "Fear not, for I am with you; be not dismayed, for I am your God; I will strengthen you, I will help you, I will uphold you with my righteous right hand.", "theme": "Assurance"},
    {"verse": "John 3:16", "text": "For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.", "theme": "Salvation"},
    {"verse": "Romans 5:8", "text": "But God shows his love for us in that while we were still sinners, Christ died for us.", "theme": "Redemption"},
    {"verse": "Psalm 139:14", "text": "I praise you, for I am fearfully and wonderfully made. Wonderful are your works; my soul knows it very well.", "theme": "Identity"},
    {"verse": "Micah 6:8", "text": "He has told you, O man, what is good; and what does the Lord require of you but to do justice, and to love kindness, and to walk humbly with your God?", "theme": "Justice"},
    {"verse": "Matthew 11:28", "text": "Come to me, all who labor and are heavy laden, and I will give you rest.", "theme": "Rest"},
    {"verse": "Lamentations 3:22-23", "text": "The steadfast love of the Lord never ceases; his mercies never come to an end; they are new every morning; great is your faithfulness.", "theme": "Faithfulness"},
]

# Verse-themed image URLs (royalty-free Christian imagery)
VERSE_IMAGES = [
    "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80",  # Bible open
    "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80",  # Cross sunset
    "https://images.unsplash.com/photo-1445445290350-18a3b86e0b5a?w=800&q=80",  # Light rays
    "https://images.unsplash.com/photo-1508672019048-805c876b67e2?w=800&q=80",  # Sunrise ocean
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80",  # Golden sunrise field
    "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=800&q=80",  # Forest light
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80",  # Mountain peak
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&q=80",  # Lake mountains
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=800&q=80",  # Sunbeam forest
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80",  # Golden field
]


def fetch_truth_is_calling_shorts():
    """Scrape RANDOM YouTube Shorts from the Truth Is Calling channel (not the latest)."""
    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(TRUTH_IS_CALLING_YOUTUBE["shorts_url"], headers=headers, timeout=15)
        resp.raise_for_status()

        # Extract Shorts video IDs (they appear in /shorts/ URLs in the page)
        shorts_ids = re.findall(r'/shorts/([a-zA-Z0-9_-]{11})', resp.text)
        unique_ids = list(dict.fromkeys(shorts_ids))  # Remove duplicates, preserve order

        # Extract Shorts titles using overlayMetadata pattern (most reliable for Shorts)
        titles = re.findall(r'"overlayMetadata":\{"primaryText":\{"content":"([^"]+)"', resp.text)
        video_titles = list(dict.fromkeys(titles))  # Remove duplicates, preserve order

        # Build list of all available shorts with their titles
        all_shorts = []
        for i, vid in enumerate(unique_ids):
            title = video_titles[i] if i < len(video_titles) else "Truth Is Calling Short"
            all_shorts.append((vid, title))

        # Skip the first 2 (most recent) and pick randomly from the rest
        # This ensures we show older/refresher content, not what's already on the Home Screen
        older_shorts = all_shorts[2:] if len(all_shorts) > 2 else all_shorts

        # Use day of year as seed so the same shorts show all day, but change daily
        day_seed = datetime.now().timetuple().tm_yday + datetime.now().year
        rng = random.Random(day_seed)
        max_items = min(TRUTH_IS_CALLING_YOUTUBE["max_items"], len(older_shorts))
        selected = rng.sample(older_shorts, max_items)

        for vid, title in selected:
            thumbnail = f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"
            shorts_url = f"https://www.youtube.com/shorts/{vid}"

            content_html = f'''
            <div style="text-align:center;">
                <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #c9a84c; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; text-align: center;">
                    <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">\u271d TRUTH IS CALLING | YouTube Short</span>
                </div>
                <p><strong>{escape(title)}</strong></p>
                <p style="color: #666;">From Truth Is Calling</p>
                <iframe width="100%" height="560" 
                    src="https://www.youtube.com/embed/{vid}" 
                    frameborder="0" allowfullscreen></iframe>
                <p style="margin-top: 10px;"><a href="{escape(shorts_url)}" style="color: #c9a84c; font-weight: bold;">Watch on YouTube \u2192</a></p>
            </div>
            '''

            items.append({
                "source_name": "Truth Is Calling",
                "category": "Your Shorts",
                "title": f"\u271d {title}",
                "url": shorts_url,
                "date": datetime.now(timezone.utc).isoformat(),
                "author": "Truth Is Calling",
                "summary": f"Watch this YouTube Short from Truth Is Calling: {title}",
                "content": content_html,
                "thumbnail": thumbnail,
            })

    except Exception as e:
        print(f"  \u26a0 Error fetching Truth Is Calling Shorts: {e}", file=sys.stderr)

    return items


def fetch_truth_is_calling_article():
    """Scrape a random article from truthiscalling.us and include its image."""
    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Get the articles listing page
        resp = requests.get(TRUTH_IS_CALLING_ARTICLES["url"], headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find all article title links
        all_articles = []
        for link in soup.find_all('a', id=lambda x: x and 'lnkBlogTitle' in str(x)):
            title = link.get_text(strip=True)
            href = link.get('href', '')
            if href and not href.startswith('http'):
                href = 'https://www.truthiscalling.us' + href
            if title and href:
                all_articles.append({'title': title, 'url': href})

        if not all_articles:
            return items

        # Pick 1 random article using day-of-year seed (changes daily)
        day_seed = datetime.now().timetuple().tm_yday + datetime.now().year + 999  # offset from shorts seed
        rng = random.Random(day_seed)
        selected = rng.sample(all_articles, min(TRUTH_IS_CALLING_ARTICLES["max_items"], len(all_articles)))

        for article_info in selected:
            try:
                # Fetch the individual article page to get image and description
                art_resp = requests.get(article_info['url'], headers=headers, timeout=10)
                art_soup = BeautifulSoup(art_resp.text, 'html.parser')

                # Get og:image (best quality article image)
                og_img = art_soup.find('meta', attrs={'property': 'og:image'})
                thumbnail = og_img.get('content', '') if og_img else ''

                # Fallback: find the article's main image (alt="temp-post-image")
                if not thumbnail:
                    img_tag = art_soup.find('img', alt='temp-post-image')
                    if img_tag:
                        thumbnail = img_tag.get('src', '')

                # Get meta description
                meta_desc = art_soup.find('meta', attrs={'name': 'description'})
                desc = meta_desc.get('content', '').strip() if meta_desc else ''
                if not desc:
                    desc = f"Read \"{article_info['title']}\" on Truth Is Calling."

                content_html = f'''
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; line-height: 1.6;">
                    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #c9a84c; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; text-align: center;">
                        <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">\u271d TRUTH IS CALLING | Article</span>
                    </div>
                    {f'<div style="text-align:center; margin-bottom: 16px;"><img src="{escape(thumbnail)}" style="width: 100%; max-width: 600px; height: auto; border-radius: 8px; object-fit: cover;" alt="{escape(article_info["title"])}" /></div>' if thumbnail else ''}
                    <p style="font-size: 16px; color: #333;">{escape(desc)}</p>
                    <div style="margin-top: 20px; text-align: center;">
                        <a href="{escape(article_info['url'])}" style="color: #c9a84c; text-decoration: none; font-weight: bold; font-size: 16px;">Read Full Article on TruthIsCalling.us \u2192</a>
                    </div>
                </div>
                '''

                items.append({
                    "source_name": "Truth Is Calling",
                    "category": "Your Article",
                    "title": f"\u271d {article_info['title']}",
                    "url": article_info['url'],
                    "date": datetime.now(timezone.utc).isoformat(),
                    "author": "Truth Is Calling",
                    "summary": desc[:300],
                    "content": content_html,
                    "thumbnail": thumbnail,
                })
            except Exception as e:
                print(f"    \u26a0 Error fetching article '{article_info['title']}': {e}", file=sys.stderr)
                continue

    except Exception as e:
        print(f"  \u26a0 Error fetching Truth Is Calling articles: {e}", file=sys.stderr)

    return items


def fetch_feed(source):
    """Fetch and parse an RSS feed, returning parsed items."""
    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (TruthIsCallingApp/1.0; Christian Content Aggregator)'
        }
        resp = requests.get(source["url"], headers=headers, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        for entry in feed.entries[:source["max_items"]]:
            item = {
                "source_name": source["name"],
                "category": source["category"],
                "title": entry.get("title", "Untitled"),
                "url": entry.get("link", ""),
                "date": "",
                "author": source["name"],
                "summary": "",
                "content": "",
                "thumbnail": "",
            }

            # Parse date
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    item["date"] = dt.isoformat()
                except:
                    item["date"] = datetime.now(timezone.utc).isoformat()
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    item["date"] = dt.isoformat()
                except:
                    item["date"] = datetime.now(timezone.utc).isoformat()
            else:
                item["date"] = datetime.now(timezone.utc).isoformat()

            # Get author
            if hasattr(entry, "author") and entry.author:
                item["author"] = entry.author

            # Get summary
            if hasattr(entry, "summary") and entry.summary:
                # Strip HTML tags for summary
                clean = re.sub(r'<[^>]+>', '', entry.summary)
                item["summary"] = clean[:300].strip()

            # Get content
            content_html = ""
            if hasattr(entry, "content") and entry.content:
                content_html = entry.content[0].get("value", "")
            elif hasattr(entry, "summary") and entry.summary:
                content_html = entry.summary

            # For YouTube videos, create embedded content
            if source["category"] == "Video":
                video_id = ""
                if "youtube.com/watch" in item["url"]:
                    video_id = re.search(r'v=([^&]+)', item["url"])
                    if video_id:
                        video_id = video_id.group(1)
                elif "yt:video:" in str(entry.get("id", "")):
                    video_id = entry.get("id", "").replace("yt:video:", "")

                if video_id:
                    item["thumbnail"] = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    content_html = f'''
                    <div style="text-align:center;">
                        <p><strong>{escape(item["title"])}</strong></p>
                        <p>From {escape(source["name"])}</p>
                        <iframe width="100%" height="315" 
                            src="https://www.youtube.com/embed/{video_id}" 
                            frameborder="0" allowfullscreen></iframe>
                        <p>{escape(item.get("summary", ""))}</p>
                        <p><a href="{escape(item["url"])}">Watch on YouTube</a></p>
                    </div>
                    '''
            else:
                # Try to extract first image from content for thumbnail
                img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
                if img_match:
                    item["thumbnail"] = img_match.group(1)

                # Also check for media:thumbnail or media:content
                if not item["thumbnail"]:
                    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                        item["thumbnail"] = entry.media_thumbnail[0].get("url", "")
                    elif hasattr(entry, "media_content") and entry.media_content:
                        item["thumbnail"] = entry.media_content[0].get("url", "")

                # Check enclosures
                if not item["thumbnail"] and hasattr(entry, "enclosures") and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image/"):
                            item["thumbnail"] = enc.get("href", "")
                            break

            # Build article content with source attribution
            styled_content = f'''
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #333; line-height: 1.6;">
                <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #c9a84c; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; text-align: center;">
                    <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">📖 {escape(source["category"])} | {escape(source["name"])}</span>
                </div>
                {content_html}
                <div style="margin-top: 20px; padding-top: 12px; border-top: 1px solid #ddd; text-align: center;">
                    <a href="{escape(item["url"])}" style="color: #c9a84c; text-decoration: none; font-weight: bold;">Read Full Article →</a>
                </div>
            </div>
            '''

            item["content"] = styled_content
            items.append(item)

    except Exception as e:
        print(f"  ⚠ Error fetching {source['name']}: {e}", file=sys.stderr)

    return items


def get_daily_verse():
    """Get the verse of the day based on day of year."""
    day_of_year = datetime.now().timetuple().tm_yday
    verse_data = DAILY_VERSES[day_of_year % len(DAILY_VERSES)]
    image_url = VERSE_IMAGES[day_of_year % len(VERSE_IMAGES)]

    today_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    content = f'''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px 20px; border-radius: 12px; color: white;">
            <div style="font-size: 14px; color: #c9a84c; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">✝ Verse of the Day</div>
            <div style="font-size: 13px; color: #8899aa; margin-bottom: 15px;">{today_str}</div>
            <div style="font-size: 20px; font-style: italic; line-height: 1.5; color: #e8e8e8; margin: 20px 0;">
                "{escape(verse_data["text"])}"
            </div>
            <div style="font-size: 16px; color: #c9a84c; font-weight: bold; margin-top: 15px;">
                — {escape(verse_data["verse"])}
            </div>
            <div style="margin-top: 15px; font-size: 12px; color: #8899aa;">
                Theme: {escape(verse_data["theme"])}
            </div>
        </div>
        <div style="margin-top: 20px;">
            <img src="{image_url}" style="width: 100%; border-radius: 8px; max-height: 300px; object-fit: cover;" alt="Daily Inspiration" />
        </div>
        <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #c9a84c;">
            <p style="font-size: 14px; color: #555; margin: 0;">
                Take a moment to reflect on this verse today. How does the theme of 
                <strong>{escape(verse_data["theme"])}</strong> speak to your life right now?
            </p>
        </div>
    </div>
    '''

    return {
        "source_name": "Truth Is Calling",
        "category": "Verse of the Day",
        "title": f"📖 {verse_data['verse']} — {verse_data['theme']}",
        "url": f"https://www.biblegateway.com/passage/?search={verse_data['verse'].replace(' ', '+')}&version=ESV",
        "date": datetime.now(timezone.utc).isoformat(),
        "author": "Truth Is Calling",
        "summary": verse_data["text"],
        "content": content,
        "thumbnail": image_url,
    }


def build_gb_article(item, index):
    """Convert a feed item into Good Barber Custom Article Feed format."""
    # Generate a unique ID
    unique_str = f"{item['title']}-{item['date']}-{item['url']}"
    item_id = hashlib.md5(unique_str.encode()).hexdigest()[:12]

    thumbnail = item.get("thumbnail", "")
    # Use a fallback image if no thumbnail
    if not thumbnail:
        fallback_idx = index % len(VERSE_IMAGES)
        thumbnail = VERSE_IMAGES[fallback_idx]

    article = {
        "id": item_id,
        "type": "article",
        "subtype": "custom",
        "title": item["title"],
        "url": item.get("url", ""),
        "date": item.get("date", datetime.now(timezone.utc).isoformat()),
        "author": item.get("author", item.get("source_name", "Truth Is Calling")),
        "summary": item.get("summary", "")[:300],
        "content": item.get("content", ""),
        "thumbnail": thumbnail,
        "smallThumbnail": thumbnail,
        "largeThumbnail": thumbnail,
        "commentsEnabled": False,
        "categories": [item.get("category", "Daily Feed")],
        "images": []
    }

    # Add thumbnail to images array
    if thumbnail:
        article["images"].append({
            "url": thumbnail,
            "id": f"img-{item_id}"
        })

    return article


def generate_feed():
    """Main function to generate the Good Barber JSON feed."""
    print("🙏 Truth Is Calling — Daily Christian Content Feed Generator")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_items = []

    # 1. Add Verse of the Day first
    print("📖 Generating Verse of the Day...")
    verse = get_daily_verse()
    all_items.append(verse)
    print(f"  ✓ {verse['title']}")

    # 2. Fetch from all RSS sources (these go right after the verse)
    print("\n📡 Fetching from Christian sources...")
    for source in SOURCES:
        print(f"  → {source['name']}...", end=" ")
        items = fetch_feed(source)
        if items:
            all_items.extend(items)
            print(f"✓ ({len(items)} items)")
        else:
            print("✗ (no items)")

    # 3. Fetch Truth Is Calling YouTube Shorts (placed at the END of the feed)
    print("\n\u271d Fetching YOUR content (Truth Is Calling)...")
    print("  \u2192 Random YouTube Shorts...", end=" ")
    tic_shorts = fetch_truth_is_calling_shorts()
    if tic_shorts:
        all_items.extend(tic_shorts)
        print(f"\u2713 ({len(tic_shorts)} random shorts — placed at end of feed)")
    else:
        print("\u2717 (no shorts found)")

    # 4. Convert to Good Barber format
    print(f"\n📦 Building Good Barber feed with {len(all_items)} items...")
    gb_articles = []
    for i, item in enumerate(all_items):
        gb_articles.append(build_gb_article(item, i))

    feed_data = {"items": gb_articles}

    # 4. Write to file
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "articles.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Feed generated: {output_path}")
    print(f"   Total articles: {len(gb_articles)}")

    # Also write a simple index.html
    index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Truth Is Calling — Daily Christian Feed</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a1a; color: #e8e8e8; min-height: 100vh; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; margin-bottom: 30px; }}
        .header h1 {{ color: #c9a84c; font-size: 24px; margin-bottom: 8px; }}
        .header p {{ color: #8899aa; font-size: 14px; }}
        .feed-url {{ background: #1a1a2e; padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; font-family: monospace; font-size: 12px; color: #c9a84c; border: 1px solid #2a2a3e; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0; }}
        .stat {{ background: #1a1a2e; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-num {{ font-size: 24px; color: #c9a84c; font-weight: bold; }}
        .stat-label {{ font-size: 12px; color: #8899aa; margin-top: 4px; }}
        .footer {{ text-align: center; padding: 20px; color: #556; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✝ TRUTH IS CALLING</h1>
            <p>John 16:37</p>
            <p style="margin-top: 10px;">Daily Christian Content Feed</p>
        </div>
        <div class="feed-url">
            Feed URL: articles.json
        </div>
        <div class="stats">
            <div class="stat">
                <div class="stat-num">{len(gb_articles)}</div>
                <div class="stat-label">Articles Today</div>
            </div>
            <div class="stat">
                <div class="stat-num">{len(SOURCES)}</div>
                <div class="stat-label">Sources</div>
            </div>
        </div>
        <div class="footer">
            <p>Last updated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
            <p>Feed auto-updates every 8 hours</p>
        </div>
    </div>
</body>
</html>'''

    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"   Landing page: {index_path}")
    print("\n🎉 Done! Feed is ready for Good Barber Custom Article Feed section.")

    return feed_data


if __name__ == "__main__":
    generate_feed()
