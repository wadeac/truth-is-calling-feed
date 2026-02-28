# Truth Is Calling — Daily Christian Content Feed

An automated RSS feed aggregator that curates Christian content daily from trusted sources. Designed to integrate with the **Truth Is Calling** Good Barber app so content rotates automatically without manual effort.

## What It Does

This system automatically pulls fresh content every day from 12+ Christian sources across multiple categories:

| Category | Sources | Items/Day |
|----------|---------|-----------|
| **Verse of the Day** | Bible Gateway (31 rotating verses) | 1 |
| **Devotional** | Our Daily Bread, WELS Daily Devotions, Harvest (Greg Laurie) | 5 |
| **Article** | Desiring God | 2 |
| **Teaching** | Ligonier Ministries | 2 |
| **News** | Christianity Today, Faithwire | 4 |
| **Culture** | Relevant Magazine | 1 |
| **Bible Study** | Bible Gateway Blog | 1 |
| **Video** | The Bible Project, Ascension Presents, InspiringPhilosophy | 3 |

The feed includes **images/thumbnails** for each item and is formatted as standard RSS 2.0 with `media:thumbnail` tags for rich display in Good Barber.

## Quick Start

### Option 1: GitHub Pages (Recommended — Free, Auto-Updates Daily)

1. Push this repository to GitHub
2. Enable **GitHub Pages** (Settings → Pages → Source: `docs` folder)
3. The GitHub Action runs daily at 6:00 AM UTC and regenerates `docs/feed.xml`
4. Your feed URL will be: `https://<username>.github.io/<repo-name>/feed.xml`

### Option 2: Run the Flask Server

```bash
pip install -r requirements.txt
python feed_server.py
# Feed available at http://localhost:5000/feed.xml
```

### Option 3: Generate Static Feed Manually

```bash
pip install feedparser requests python-dateutil
python generate_static_feed.py docs
# Output: docs/feed.xml
```

## Adding to Good Barber

1. Log in to your Good Barber back office
2. Go to **Design & Structure → Structure → Sections**
3. Click **+ Add a section**
4. Click **"Load more"** to see all section types
5. Select **RSS**
6. Name it something like **"Daily Christian Feed"** or **"Today's Inspiration"**
7. Paste your feed URL (e.g., `https://<username>.github.io/<repo>/feed.xml`)
8. Click **Add**
9. **Drag the new section to the top** of your section list

## Customizing Sources

Edit the `SOURCES` list in either `feed_server.py` or `generate_static_feed.py`:

```python
SOURCES = [
    {
        "name": "Source Name",
        "url": "https://example.com/feed/",
        "category": "Devotional",  # Category label shown in feed
        "max_items": 2,            # Max items to pull from this source
    },
    # Add more sources...
]
```

### Adding YouTube Channels

YouTube channels have RSS feeds at:
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

To find a channel's ID:
1. Go to the YouTube channel page
2. View page source or check the URL
3. The channel ID starts with `UC...`

## File Structure

```
├── feed_server.py              # Flask web server (dynamic feed)
├── generate_static_feed.py     # Static feed generator script
├── index.html                  # Landing page for GitHub Pages
├── requirements.txt            # Python dependencies
├── .github/
│   └── workflows/
│       └── daily-feed.yml      # GitHub Actions daily automation
└── docs/
    ├── feed.xml                # Generated RSS feed (auto-updated)
    └── index.html              # Landing page copy
```

## How Content Rotates

- **Sources publish new content daily** — the feed automatically picks up the latest items
- **Verse of the Day** rotates through 31 key Bible verses based on the day of the year
- **Images rotate** with each new article/video from the sources
- The feed refreshes every 4 hours (server mode) or daily (GitHub Actions mode)
- Good Barber syncs the RSS feed periodically, so new content appears in your app automatically

## License

This project is provided for personal/ministry use. Content is sourced from public RSS feeds of the respective publishers.
