# Truth Is Calling — Daily Christian Feed: Complete Setup Guide

## Overview

I have built an automated RSS feed system that aggregates Christian content from 12+ trusted sources and rotates it daily. This feed is designed to plug directly into your Good Barber app as an RSS section at the top of your home screen, replacing the need to manually find articles, YouTube videos, and devotionals.

## What the Feed Includes (19 items, refreshed daily)

| Category | Source | Description |
|----------|--------|-------------|
| **Verse of the Day** | Bible Gateway | Rotates through 31 key Bible verses with beautiful imagery |
| **Devotional** | Our Daily Bread | Classic daily devotional readings |
| **Devotional** | WELS Daily Devotions | Lutheran daily devotional content |
| **Devotional** | Harvest (Greg Laurie) | Daily devotions from Pastor Greg Laurie |
| **Article** | Desiring God | John Piper's ministry — deep theological articles |
| **Teaching** | Ligonier Ministries | R.C. Sproul's ministry — reformed teaching |
| **News** | Christianity Today | Major Christian news and reporting |
| **News** | Faithwire | Faith-based news and current events |
| **Culture** | Relevant Magazine | Faith, culture, and current issues |
| **Bible Study** | Bible Gateway Blog | Bible study resources and insights |
| **Video** | The Bible Project | Animated Bible explainer videos |
| **Video** | Ascension Presents | Catholic teaching and apologetics |
| **Video** | InspiringPhilosophy | Apologetics and philosophy videos |

Each item includes a **thumbnail image**, so your Good Barber app will display rich visual cards just like your existing "Reflections" section.

---

## Your Feed URL (Currently Live)

The feed is currently running and accessible at:

```
https://5000-ix0jpxicysjxyqy0yv15l-a803f0a7.us2.manus.computer/feed.xml
```

**Note:** This temporary URL will stop working when the sandbox shuts down. For a permanent solution, follow the GitHub Pages setup below.

---

## Permanent Setup: GitHub Pages (Free, Auto-Updates Daily)

Your code has been pushed to your GitHub repository:
**https://github.com/wadeac/truth-is-calling-feed**

### Step 1: Enable GitHub Pages

1. Go to **https://github.com/wadeac/truth-is-calling-feed/settings/pages**
2. Under **Source**, select **Deploy from a branch**
3. Set **Branch** to `master` and **Folder** to `/docs`
4. Click **Save**
5. Wait 1-2 minutes for deployment

Your permanent feed URL will be:
```
https://wadeac.github.io/truth-is-calling-feed/feed.xml
```

### Step 2: Add the GitHub Actions Workflow

The workflow file couldn't be pushed automatically due to permissions. You need to add it manually:

1. Go to your repo: https://github.com/wadeac/truth-is-calling-feed
2. Click **Add file → Create new file**
3. Name it: `.github/workflows/daily-feed.yml`
4. Paste the following content:

```yaml
name: Generate Daily Christian Feed

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install feedparser requests python-dateutil

      - name: Generate feed
        run: python generate_static_feed.py docs

      - name: Copy index.html to docs
        run: cp index.html docs/index.html 2>/dev/null || true

      - name: Commit and push updated feed
        run: |
          git config user.name "GitHub Actions Bot"
          git config user.email "actions@github.com"
          git add docs/feed.xml docs/index.html
          git diff --staged --quiet || git commit -m "Update daily feed - $(date -u +%Y-%m-%d)"
          git push
```

5. Click **Commit new file**

### Step 3: Test the Workflow

1. Go to **Actions** tab in your repository
2. Click on **"Generate Daily Christian Feed"** workflow
3. Click **"Run workflow"** → **"Run workflow"** (green button)
4. Wait for it to complete (about 1-2 minutes)
5. Verify the feed at your GitHub Pages URL

---

## Adding the Feed to Good Barber

### Step 1: Add RSS Section

1. Log in to your Good Barber back office
2. Go to **Design & Structure → Structure → Sections**
3. Click **+ Add a section** in the right panel
4. Click **"Load more"** to see all section types
5. Select **RSS**

### Step 2: Configure the Section

1. **Section name:** "Daily Inspiration" (or "Today's Christian Feed", etc.)
2. **RSS URL:** Paste your GitHub Pages feed URL:
   ```
   https://wadeac.github.io/truth-is-calling-feed/feed.xml
   ```
3. Click **Add**

### Step 3: Position at the Top

1. In the Sections list, **drag your new RSS section to the very top** (above "Reflections")
2. This ensures it appears first when users open the app

### Step 4: Style the Section (Optional)

- Choose a display template that shows images (card view or list with thumbnails)
- The feed includes `media:thumbnail` and `enclosure` tags, so Good Barber should automatically display images

---

## How It Works Day-to-Day

Once set up, the system is fully automated:

1. **Every day at midnight MST (6 AM UTC)**, GitHub Actions runs the feed generator
2. The script fetches the latest content from all 12+ sources
3. A new `feed.xml` is generated with fresh content and committed to your repo
4. GitHub Pages serves the updated file
5. Good Barber periodically syncs the RSS feed and displays the new content in your app

**You don't need to do anything** — content rotates automatically as sources publish new material.

---

## Customization

### Adding or Removing Sources

Edit `generate_static_feed.py` in your GitHub repo. The `SOURCES` list at the top controls which feeds are included:

```python
{
    "name": "Source Name",
    "url": "https://example.com/feed/",
    "category": "Devotional",
    "max_items": 2,
}
```

### Adding YouTube Channels

YouTube channels have RSS feeds at:
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

### Changing the Verse of the Day Pool

The `DAILY_VERSES` list contains 31 verses that rotate by day of the year. Add or modify verses as needed.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Feed not updating | Go to Actions tab → manually run the workflow |
| Images not showing | Ensure Good Barber section uses a template with image support |
| Feed URL not working | Check GitHub Pages is enabled (Settings → Pages) |
| Want to force refresh | Go to Actions → Run workflow manually |
