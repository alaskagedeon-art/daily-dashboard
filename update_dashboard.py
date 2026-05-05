#!/usr/bin/env python3
import os
import re
import json
from datetime import date
import anthropic

TAX_DUE = date(2026, 4, 15)


def days_past_due():
    return (date.today() - TAX_DUE).days


def build_narratives_html(narratives):
    color_map = {"red": "nc-red", "gold": "nc-gold", "green": "nc-green", "muted": "nc-muted"}
    html = ""
    for i, n in enumerate(narratives, 1):
        cls = color_map.get(n.get("color", "muted"), "nc-muted")
        tag = n["tag"].replace("·", "&middot;")
        html += f"""
        <div class="narrative-card {cls}">
          <div class="nc-eyebrow">
            <span class="nc-num">{i:02d}</span>
            <span class="nc-tag">{tag}</span>
          </div>
          <div class="nc-title">{n["title"]}</div>
          <div class="nc-body">{n["body"]}</div>
          <div class="nc-footer">
            <div class="nc-footer-item">Temp<span>{n["temp"]}</span></div>
            <div class="nc-footer-item">Signal<span>{n["signal"]} / 5</span></div>
          </div>
        </div>"""
    return html


def build_priorities_html(priorities, news_bullets):
    color_map = {"red": "pi-red", "gold": "pi-gold", "green": "pi-green"}
    html = ""
    for p in priorities:
        cls = color_map.get(p.get("color", "green"), "pi-green")
        html += f"""
        <div class="priority-item {cls}">
          <div class="pi-title">{p["title"]}</div>
          <div class="pi-body">{p["body"]}</div>
        </div>"""
    html += '\n        <div class="news-list">\n          <div class="section-title">Quick News</div>'
    for b in news_bullets:
        html += f'\n          <div class="news-bullet"><span class="news-dot"></span><span>{b}</span></div>'
    html += "\n        </div>"
    return html


def generate_content(days_overdue):
    client = anthropic.Anthropic()
    today = date.today().strftime("%B %d, %Y")

    prompt = f"""Today is {today}. Generate fresh daily dashboard content for Alaska Gedeon — a music/nightlife executive in Los Angeles. He runs EVNMORE Sundays (weekly WeHo residency, 600+ guests, 10M+ IG reach), Reframe (executive coaching + events), and 2Sags Productions (music A&R).

Return ONLY valid JSON, no markdown fences:
{{
  "narratives": [
    {{
      "tag": "Topic · Subtopic · Theme",
      "title": "Short punchy title",
      "body": "2-3 sentences: what happened, why it matters now, how it connects to culture/internet/WeHo audience",
      "temp": "Emotion + Emotion",
      "signal": 4,
      "color": "red"
    }}
  ],
  "priorities": [
    {{
      "title": "Action item title",
      "body": "One sentence of urgency and specific context",
      "color": "red"
    }}
  ],
  "news_bullets": ["One line news item"]
}}

Rules:
- 5 narratives. color: red=urgent/political/conflict, gold=culture/money/class, green=opportunity/crypto/upside, muted=celebrity/entertainment
- Signal 1-5 (5=must-act today for content)
- 6 priorities: 2 red (taxes = #{days_overdue} days past April 15 due date ALWAYS first, plus one news-driven urgent), 2 gold (this week), 2 green (ongoing: Reframe LLC, brand outreach)
- 7 news bullets, punchy, no fluff
- Write for WeHo nightlife/culture audience aged 18-40
- Base narratives on real events happening around {today}"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    text = re.sub(r'^```\w*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


def main():
    days_overdue = days_past_due()

    with open("index.html", "r") as f:
        html = f.read()

    html = re.sub(r'Taxes \d+ Days? Past Due', f'Taxes {days_overdue} Days Past Due', html)

    content = generate_content(days_overdue)

    narratives_html = build_narratives_html(content["narratives"])
    html = re.sub(
        r'<!-- NARRATIVES-START -->.*?<!-- NARRATIVES-END -->',
        f'<!-- NARRATIVES-START -->{narratives_html}\n        <!-- NARRATIVES-END -->',
        html, flags=re.DOTALL
    )

    priorities_html = build_priorities_html(content["priorities"], content["news_bullets"])
    html = re.sub(
        r'<!-- PRIORITIES-START -->.*?<!-- PRIORITIES-END -->',
        f'<!-- PRIORITIES-START -->{priorities_html}\n        <!-- PRIORITIES-END -->',
        html, flags=re.DOTALL
    )

    with open("index.html", "w") as f:
        f.write(html)

    print(f"Updated for {date.today()} — taxes {days_overdue} days past due")


if __name__ == "__main__":
    main()
