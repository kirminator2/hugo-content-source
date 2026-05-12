#!/usr/bin/env python3
"""
Hugo article generator + deploy + IndexNow for telegraph_admin.
Creates SEO-optimized Hugo articles with full content, CTA blocks,
Telegram channel links, and referral links.
"""

import os
import subprocess
import urllib.request
import json
import re
import random
from datetime import datetime

HUGO_SOURCE = os.path.expanduser("~/hugo-content-source")
SITE_URL = "https://gptnews.github.io"
INDEXNOW_KEY = "b7f3a9c1d4e8f2a6b0c3d5e7f9a1b4c8d0e2f6a3"

# Telegram channels per section
CHANNELS = {
    'crypto': {'name': '🐋 Crypto Whale Signals', 'url': 'https://t.me/forex_signals_fast'},
    'forex': {'name': '📈 Forex Trading Signals', 'url': 'https://t.me/forex_signals_fast'},
    'ai':    {'name': '🤖 AI & Neural Networks', 'url': 'https://t.me/forex_signals_fast'},
}

REF_LINKS = [
    ('Bybit', 'https://www.bybit.com/invite?ref=ZWEP5M'),
    ('Antarctic Wallet', 'https://t.me/antarctic_wallet_bot/app?startapp=ref_10c262774a'),
]

# Proxy for external requests
PROXY = "http://g66dg3:MHD5yH@213.139.222.226:9591"


# ─── Helpers ─────────────────────────────────────────────

def _strip_html(html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html)
    for e in ['&nbsp;', '&amp;', '&lt;', '&gt;', '&quot;', '&#39;']:
        text = text.replace(e, ' ')
    return re.sub(r'\s+', ' ', text).strip()


def _get_description(content: str, max_len: int = 200) -> str:
    text = _strip_html(content)
    if len(text) <= max_len:
        return text
    for c in ('.', '!', '?'):
        idx = text.rfind(c, 0, max_len)
        if idx > max_len // 2:
            return text[:idx + 1]
    return text[:max_len].rstrip() + '...'


def _get_content_excerpt(html: str, words: int = 120) -> str:
    """Extract first N words of clean content for the Hugo article body"""
    text = _strip_html(html)
    parts = text.split()
    excerpt = ' '.join(parts[:words])
    if len(parts) > words:
        excerpt += '...'
    return excerpt


def slugify(title: str) -> str:
    slug = title.lower()
    cyr_map = dict(zip(
        'абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
        'abvgdeejzijklmnoprstufkhcchshshchbyyeyuya'
    ))
    slug = ''.join(cyr_map.get(c, c) for c in slug)
    slug = re.sub(r'[^a-z0-9-]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def _detect_language(text: str) -> str:
    """Detect if text is Russian or English"""
    cyrillic = sum(1 for c in text if 'а' <= c.lower() <= 'я')
    total = len(text.strip())
    if total > 0 and cyrillic / total > 0.05:
        return 'ru'
    return 'en'


def _build_tags(section: str, title: str, content: str) -> list:
    """Generate relevant tags from article data"""
    tags = [section]
    text = (title + ' ' + _strip_html(content)).lower()
    
    keyword_map = {
        'bitcoin|btc|bitcoin|eth|ethereum|ripple|xrp|solana|sol|cardano|ada': 'crypto',
        'whale|кит|киты|кошелек|wallet|кошельки|transfers|перевод': 'whales',
        'trading|трейдинг|signal|сигнал|анализ|analysis': 'trading',
        'forex|форекс|eurusd|gbpusd|usdjpy|валют': 'forex',
        'ai|нейрон|нейросет|gpt|chatgpt|llm|ии|искусствен': 'ai',
        'defi|дефи|nft|token|токен|дроп|airdrop': 'defi',
        'regulation|регул|sec|закон|binance|bybit': 'regulation',
    }
    
    for pattern, tag in keyword_map.items():
        if re.search(pattern, text):
            if tag not in tags:
                tags.append(tag)
    
    return tags


# ─── Article Generation ─────────────────────────────────

def generate_article(article: dict) -> str:
    title = article.get('title', 'Untitled')
    section = article.get('section', 'crypto')
    telegraph_url = article.get('telegraph_url', '')
    content_html = article.get('content', '')
    image = article.get('image_path', '')
    author = article.get('author_name', 'Admin')

    lang = _detect_language(title + ' ' + _strip_html(content_html))
    
    section_dir = f"content/{section}"
    if lang == 'ru':
        section_dir = f"content/ru/{section}"
    
    full_dir = os.path.join(HUGO_SOURCE, section_dir)
    os.makedirs(full_dir, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(full_dir, filename)

    description = _get_description(content_html)
    excerpt = _get_content_excerpt(content_html, 150)
    tags = _build_tags(section, title, content_html)
    tags_yaml = '\n'.join(f'  - "{t}"' for t in tags)
    categories_yaml = f'  - "{section}"'

    chan = CHANNELS.get(section, CHANNELS['crypto'])
    ref = random.choice(REF_LINKS)

    # Build article body
    body = f"""{excerpt}

---

**[📖 Читать полный анализ на Telegraph →]({telegraph_url})**

---

## 📢 Присоединяйся к нам!

[{chan['name']}]({chan['url']}) — актуальные сигналы, аналитика и инсайты каждый день.

💎 **Торгуй с лучшими условиями:** [{ref[0]}]({ref[1]})

*Источник: [Crypto Whale Watch]({SITE_URL})* | [Категория: {section}]({SITE_URL}/{section}/)
"""

    frontmatter = f"""---
title: "{title}"
date: {datetime.now().isoformat()}
description: "{description}"
author: "{author}"
tags:
{tags_yaml}
categories:
{categories_yaml}
telegraph_url: "{telegraph_url}"
image: "{image}"
draft: false
---

{body}
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    print(f"Created: {filepath} ({lang}, {len(tags)} tags)")
    return filename


# ─── Deploy ─────────────────────────────────────────────

def deploy():
    script = os.path.join(HUGO_SOURCE, 'deploy.sh')
    if not os.path.exists(script):
        return False
    r = subprocess.run(['bash', script], capture_output=True, text=True, timeout=120)
    print(r.stdout)
    if r.returncode != 0:
        print(f"Deploy ERR: {r.stderr}")
        return False
    return True


# ─── IndexNow ────────────────────────────────────────────

def ping_indexnow(url: str):
    """Ping Bing IndexNow with article URL"""
    try:
        payload = json.dumps({
            "host": "kirminator2.github.io",
            "key": INDEXNOW_KEY,
            "urlList": [url]
        }).encode()

        handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
        opener = urllib.request.build_opener(handler)

        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        resp = opener.open(req, timeout=15)
        print(f"✓ IndexNow pinged {url} → HTTP {resp.status}")
        return True
    except Exception as e:
        print(f"✗ IndexNow ping failed: {e}")
        return False


# ─── Pipeline ────────────────────────────────────────────

def publish_hugo_article(article: dict):
    print(f"=== Hugo pipeline article #{article.get('id')} ===")
    
    fn = generate_article(article)
    if not fn:
        return False

    if not deploy():
        return False

    path = f"/{article.get('section', 'crypto')}/{fn.replace('.md', '/')}"
    page_url = f"{SITE_URL}{path}"
    ping_indexnow(page_url)

    print(f"✓ Done: {page_url}")
    return True


if __name__ == '__main__':
    publish_hugo_article({
        'id': 1,
        'title': 'Bitcoin Whales Accumulating — 50K BTC Moved to Cold Wallets',
        'content': '<p>A new wave of Bitcoin accumulation is underway. On-chain data shows that whale wallets have moved over 50,000 BTC to cold storage in the past 48 hours. This typically signals long-term holding sentiment and reduced selling pressure. Analysts suggest this could be a precursor to a major price movement in Q3 2026.</p><p>The largest transaction involved a wallet tagged as "Unknown Whale 3Bf7..." moving 12,400 BTC to a new address. This pattern has historically preceded significant uptrends.</p>',
        'telegraph_url': 'https://telegra.ph/Bitcoin-Whales-Accumulating-05-12',
        'telegraph_path': 'Bitcoin-Whales-Accumulating-05-12',
        'section': 'crypto',
        'author_name': 'Whale Watch Analytics',
        'image_path': '',
    })
