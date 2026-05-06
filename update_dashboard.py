#!/usr/bin/env python3
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

TAX_DUE = date(2026, 4, 15)

FEEDS = [
    "https://feeds.apnews.com/rss/topnews",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.npr.org/1001/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.theguardian.com/world/rss",
]


def days_past_due():
    return (date.today() - TAX_DUE).days


def fetch_feed(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        })
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=15) as r:
            return r.read()
    except Exception as e:
        print(f"Feed failed {url}: {e}")
        return None


def parse_items(xml_bytes):
    items = []
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
            if title:
                items.append({"title": title, "desc": desc[:220] or title})
        if not items:
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "").strip()
                desc = entry.findtext("{http://www.w3.org/2005/Atom}summary", "").strip()
                if title:
                    items.append({"title": title, "desc": desc[:220] or title})
    except Exception:
        pass
    return items


def get_items():
    all_items, seen = [], set()
    for url in FEEDS:
        data = fetch_feed(url)
        if data:
            for item in parse_items(data):
                key = item["title"][:60]
                if key not in seen:
                    seen.add(key)
                    all_items.append(item)
        if len(all_items) >= 20:
            break
    return all_items[:20]


def classify(title):
    t = title.lower()
    if any(w in t for w in ["war","attack","kill","crisis","trump","russia","china","nuclear","iran","israel","bomb","shoot"]):
        return "red"
    if any(w in t for w in ["economy","inflation","price","market","stock","tariff","trade","gdp","fed","dollar","crypto"]):
        return "gold"
    if any(w in t for w in ["tech","ai","climate","health","science","space","energy","breakthrough"]):
        return "green"
    return "muted"


def tags_for(title):
    t = title.lower()
    tags = []
    if any(w in t for w in ["trump","congress","senate","election","republican","democrat","white house"]): tags.append("Politics")
    if any(w in t for w in ["war","military","attack","russia","ukraine","iran","israel","hamas"]): tags.append("Conflict")
    if any(w in t for w in ["economy","inflation","fed","market","stock","tariff","trade"]): tags.append("Economy")
    if any(w in t for w in ["crypto","bitcoin","ethereum","solana","blockchain"]): tags.append("Crypto")
    if any(w in t for w in ["celebrity","hollywood","music","film","entertainment"]): tags.append("Culture")
    if any(w in t for w in ["tech","ai","google","apple","meta","openai","amazon"]): tags.append("Tech")
    if any(w in t for w in ["climate","weather","storm","flood","fire"]): tags.append("Climate")
    return " · ".join(tags[:3]) or "News · World · Today"


TEMPS = {"red": "Anxious + Engaged", "gold": "Curious + Concerned", "green": "Optimistic + Watching", "muted": "Amused + Observing"}


def build_narratives_html(items):
    html = ""
    for i, item in enumerate(items[:5], 1):
        color = classify(item["title"])
        html += f"""
        <div class="narrative-card nc-{color}">
          <div class="nc-eyebrow">
            <span class="nc-num">{i:02d}</span>
            <span class="nc-tag">{tags_for(item["title"])}</span>
          </div>
          <div class="nc-title">{item["title"][:80]}</div>
          <div class="nc-body">{item["desc"]}</div>
          <div class="nc-footer">
            <div class="nc-footer-item">Temp<span>{TEMPS[color]}</span></div>
            <div class="nc-footer-item">Signal<span>{"5" if color == "red" else "4"} / 5</span></div>
          </div>
        </div>"""
    return html


def build_priorities_html(days_overdue):
    return f"""
        <div class="priority-item pi-red">
          <div class="pi-title">Contact CPA about taxes — TODAY</div>
          <div class="pi-body">{days_overdue} days past the 2024 deadline. 5 prior unfiled years. A voicemail stops the bleeding.</div>
        </div>
        <div class="priority-item pi-red">
          <div class="pi-title">Post on today's top narrative</div>
          <div class="pi-body">Check the narratives — pick the highest signal story and post your take before noon.</div>
        </div>
        <div class="priority-item pi-gold">
          <div class="pi-title">EVNMORE Sunday — lock this week's activation</div>
          <div class="pi-body">Theme + any brand tie-ins. Post the event by Thursday for max reach.</div>
        </div>
        <div class="priority-item pi-gold">
          <div class="pi-title">Reframe LLC — file this week</div>
          <div class="pi-body">California LLC online, $70 via SOS website. Legal foundation for Q2 ops.</div>
        </div>
        <div class="priority-item pi-green">
          <div class="pi-title">One brand outreach email today</div>
          <div class="pi-body">Patron, Mala Mia, or Netflix — one email. Creator retainers are the Q2 revenue engine.</div>
        </div>
        <div class="priority-item pi-green">
          <div class="pi-title">WAM with Camille — schedule this week</div>
          <div class="pi-body">Weekly Accountability Meeting keeps Reframe moving. 30 min, any day.</div>
        </div>"""


def build_news_html(items):
    html = '\n        <div class="news-list">\n          <div class="section-title">Quick News</div>'
    for item in items[5:12]:
        html += f'\n          <div class="news-bullet"><span class="news-dot"></span><span>{item["title"][:120]}</span></div>'
    html += "\n        </div>"
    return html


def main():
    days_overdue = days_past_due()
    items = get_items()

    with open("index.html", "r") as f:
        html = f.read()

    html = re.sub(r"Taxes \d+ Days? Past Due", f"Taxes {days_overdue} Days Past Due", html)

    narratives_html = build_narratives_html(items)
    html = re.sub(
        r"<!-- NARRATIVES-START -->.*?<!-- NARRATIVES-END -->",
        f"<!-- NARRATIVES-START -->{narratives_html}\n        <!-- NARRATIVES-END -->",
        html, flags=re.DOTALL
    )

    priorities_html = build_priorities_html(days_overdue)
    news_html = build_news_html(items)
    html = re.sub(
        r"<!-- PRIORITIES-START -->.*?<!-- PRIORITIES-END -->",
        f"<!-- PRIORITIES-START -->{priorities_html}{news_html}\n        <!-- PRIORITIES-END -->",
        html, flags=re.DOTALL
    )

    with open("index.html", "w") as f:
        f.write(html)

    print(f"Done — {date.today()} — taxes {days_overdue} days past due — {len(items)} stories fetched")


if __name__ == "__main__":
    main()
