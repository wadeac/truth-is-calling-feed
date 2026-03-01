#!/usr/bin/env python3
"""
Flocknote Feed Transformer for Good Barber Custom Article Feed
Fetches the Flocknote RSS feed, cleans it up, and outputs a beautifully
formatted JSON file in Good Barber's Custom Article Feed format.

Feed: Truth's Calling — Holy Cross Catholic Church, Las Cruces
"""

import json
import hashlib
import feedparser
import requests
import re
import os
import sys
from datetime import datetime, timezone
from html import escape

# ─── Configuration ───────────────────────────────────────────────────────────

FLOCKNOTE_RSS = "https://rss.flocknote.com/99564"
FLOCKNOTE_GROUP = "Truth's Calling"
FLOCKNOTE_CHURCH = "Holy Cross Catholic Church"
FLOCKNOTE_LOCATION = "Las Cruces, NM"

# Themed images for different message types (rotate based on content)
THEMED_IMAGES = {
    "bible_study": [
        "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800&q=80",  # Open Bible
        "https://images.unsplash.com/photo-1529070538774-1935b8c39cda?w=800&q=80",  # Bible study
        "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&q=80",  # Reading
    ],
    "prayer": [
        "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80",  # Cross sunset
        "https://images.unsplash.com/photo-1445445290350-18a3b86e0b5a?w=800&q=80",  # Light rays
        "https://images.unsplash.com/photo-1508672019048-805c876b67e2?w=800&q=80",  # Sunrise ocean
    ],
    "announcement": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80",  # Mountain peak
        "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=800&q=80",  # Golden sunrise
        "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&q=80",  # Lake mountains
    ],
    "memorial": [
        "https://images.unsplash.com/photo-1507692049790-de58290a4334?w=800&q=80",  # Cross sunset
        "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=800&q=80",  # Sunbeam forest
    ],
    "default": [
        "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=800&q=80",  # Forest light
        "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&q=80",  # Golden field
    ],
}


def classify_message(title, description):
    """Classify the message type based on title and content keywords."""
    text = (title + " " + description).lower()

    if any(kw in text for kw in ["bible study", "thessalonians", "chapter", "study tonight", "study:", "study this"]):
        return "bible_study"
    elif any(kw in text for kw in ["prayer", "pray", "rosary", "surgery", "under the weather"]):
        return "prayer"
    elif any(kw in text for kw in ["gone home", "funeral", "services", "memorial", "passed", "rest in peace"]):
        return "memorial"
    elif any(kw in text for kw in ["update", "vote", "meeting", "event", "schedule"]):
        return "announcement"
    else:
        return "default"


def get_themed_image(msg_type, index):
    """Get a themed image based on message type and index for variety."""
    images = THEMED_IMAGES.get(msg_type, THEMED_IMAGES["default"])
    return images[index % len(images)]


def format_message_content(title, description, date_str, msg_type):
    """Create beautifully formatted HTML content for the message."""

    # Determine category label and icon
    category_labels = {
        "bible_study": ("📖 Bible Study", "#2d5016"),
        "prayer": ("🙏 Prayer Request", "#5c1a8c"),
        "memorial": ("✝ In Memoriam", "#1a1a2e"),
        "announcement": ("📢 Announcement", "#8b4513"),
        "default": ("💬 Message", "#16213e"),
    }
    label, color = category_labels.get(msg_type, ("💬 Message", "#16213e"))

    # Clean up the description text
    # Replace line breaks and clean up whitespace
    clean_desc = description.strip()
    # Convert plain text line breaks to HTML paragraphs
    paragraphs = [p.strip() for p in clean_desc.split('\n') if p.strip()]
    formatted_text = ''.join(f'<p style="margin: 8px 0; line-height: 1.7; color: #333; font-size: 15px;">{escape(p)}</p>' for p in paragraphs)

    # If it's a single block of text, make it more readable
    if len(paragraphs) <= 1:
        formatted_text = f'<p style="margin: 8px 0; line-height: 1.7; color: #333; font-size: 15px;">{escape(clean_desc)}</p>'

    content_html = f'''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #c9a84c; padding: 16px 20px; border-radius: 12px 12px 0 0; text-align: center;">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px; opacity: 0.8;">✝ {escape(FLOCKNOTE_GROUP)}</div>
            <div style="font-size: 10px; color: #8899aa;">{escape(FLOCKNOTE_CHURCH)} · {escape(FLOCKNOTE_LOCATION)}</div>
        </div>

        <!-- Category Badge -->
        <div style="background: {color}; color: white; padding: 8px 16px; text-align: center;">
            <span style="font-size: 12px; font-weight: 600; letter-spacing: 1px;">{label}</span>
        </div>

        <!-- Message Content -->
        <div style="background: #ffffff; padding: 20px 24px; border: 1px solid #e8e8e8; border-top: none;">
            <h2 style="font-size: 20px; color: #1a1a2e; margin: 0 0 12px 0; font-weight: 700; line-height: 1.3;">{escape(title)}</h2>
            <div style="font-size: 12px; color: #888; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #f0f0f0;">
                📅 {escape(date_str)} &nbsp;·&nbsp; From Wade Cornelius
            </div>
            <div style="color: #333;">
                {formatted_text}
            </div>
        </div>

        <!-- Footer -->
        <div style="background: #f8f9fa; padding: 14px 20px; border-radius: 0 0 12px 12px; border: 1px solid #e8e8e8; border-top: none; text-align: center;">
            <div style="font-size: 11px; color: #888;">
                Sent via <span style="color: #c9a84c; font-weight: 600;">Truth Is Calling</span> on Flocknote
            </div>
        </div>
    </div>
    '''

    return content_html


def build_gb_article(entry, index):
    """Convert a Flocknote RSS entry into a Good Barber Custom Article Feed item."""
    title = entry.get("title", "Message from Truth's Calling")
    link = entry.get("link", "")
    description = entry.get("description", "")
    published = entry.get("published", "")

    # Parse the date
    date_iso = datetime.now(timezone.utc).isoformat()
    date_display = datetime.now().strftime("%B %d, %Y")
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            date_iso = dt.isoformat()
            date_display = dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            pass

    # Classify the message type
    msg_type = classify_message(title, description)

    # Get themed image
    thumbnail = get_themed_image(msg_type, index)

    # Format the content
    content_html = format_message_content(title, description, date_display, msg_type)

    # Generate unique ID
    unique_str = f"flocknote-{link}-{title}"
    item_id = hashlib.md5(unique_str.encode()).hexdigest()[:12]

    # Clean summary (strip HTML, limit length)
    clean_summary = re.sub(r'<[^>]+>', '', description).strip()
    if len(clean_summary) > 200:
        clean_summary = clean_summary[:197] + "..."

    # Category display name
    category_names = {
        "bible_study": "Bible Study",
        "prayer": "Prayer",
        "memorial": "In Memoriam",
        "announcement": "Announcement",
        "default": "Message",
    }

    article = {
        "id": item_id,
        "type": "article",
        "subtype": "custom",
        "title": title,
        "url": link,
        "date": date_iso,
        "author": "Wade Cornelius",
        "summary": clean_summary,
        "content": content_html,
        "thumbnail": thumbnail,
        "smallThumbnail": thumbnail,
        "largeThumbnail": thumbnail,
        "commentsEnabled": False,
        "categories": [category_names.get(msg_type, "Message")],
        "images": [{"url": thumbnail, "id": f"img-{item_id}"}],
    }

    return article


def generate_flocknote_feed():
    """Main function to generate the cleaned-up Flocknote feed."""
    print("✝ Truth's Calling — Flocknote Feed Transformer")
    print("=" * 55)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: {FLOCKNOTE_RSS}")
    print()

    # Fetch the Flocknote RSS feed
    print("📥 Fetching Flocknote RSS feed...", end=" ")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (TruthIsCallingApp/1.0; Flocknote Feed Transformer)'
        }
        resp = requests.get(FLOCKNOTE_RSS, headers=headers, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        print(f"✓ ({len(feed.entries)} messages found)")
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

    # Convert each entry
    print("\n📝 Formatting messages...")
    gb_articles = []
    for i, entry in enumerate(feed.entries):
        title = entry.get("title", "Untitled")
        msg_type = classify_message(title, entry.get("description", ""))
        article = build_gb_article(entry, i)
        gb_articles.append(article)
        print(f"  {i+1}. [{msg_type}] {title[:60]}")

    feed_data = {"items": gb_articles}

    # Write to file
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "flocknote.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Feed generated: {output_path}")
    print(f"   Total messages: {len(gb_articles)}")
    print("\n🎉 Done! Feed is ready for Good Barber Custom Article Feed section.")

    return feed_data


if __name__ == "__main__":
    generate_flocknote_feed()
