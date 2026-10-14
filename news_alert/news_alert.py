"""대한민국 뉴스 키워드 알림.

config.json 에 적은 키워드가 들어간 최근 뉴스를 Google 뉴스(한국판) RSS 에서 찾아
PC 알림(토스트)으로 제목을 보여주고, 전체 목록은 report.html 로 저장합니다.
API 키가 필요 없습니다. 매일 아침 9시 실행은 install_windows_task.ps1 로 등록하세요.

사용법:
    python news_alert.py           # 검색 후 알림
    python news_alert.py --test    # 결과가 없어도 알림이 뜨는지 테스트
"""

import argparse
import html
import json
import os
import sys
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
SEEN_PATH = os.path.join(BASE_DIR, "seen.json")
REPORT_PATH = os.path.join(BASE_DIR, "report.html")
LOG_PATH = os.path.join(BASE_DIR, "news_alert.log")

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"


def log(message):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fetch_rss(keywords, lookback):
    # 띄어쓰기가 있는 키워드는 따옴표로 묶어 정확히 일치하는 문구로 검색
    terms = " ".join(f'"{k}"' if " " in k else k for k in keywords)
    query = urllib.parse.quote(f"{terms} when:{lookback}")
    request = urllib.request.Request(
        RSS_URL.format(query=query), headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def parse_items(rss_bytes):
    items = []
    for item in ET.fromstring(rss_bytes).iter("item"):
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        # Google 뉴스 제목은 "제목 - 언론사" 형식이므로 언론사 부분을 떼어냄
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        published = None
        pub_text = item.findtext("pubDate")
        if pub_text:
            try:
                published = parsedate_to_datetime(pub_text).astimezone()
            except (TypeError, ValueError):
                pass
        items.append(
            {
                "title": title,
                "link": (item.findtext("link") or "").strip(),
                "source": source,
                "published": published,
            }
        )
    return items


def collect(config, seen):
    keywords = config["keywords"]
    # "all": 모든 키워드가 제목에 함께 들어간 기사만 / "any": 키워드별로 따로 검색
    if config.get("match", "all") == "all":
        groups = [keywords]
    else:
        groups = [[k] for k in keywords]

    results = {}
    for group in groups:
        label = " + ".join(group)
        try:
            items = parse_items(fetch_rss(group, config.get("lookback", "1d")))
        except Exception as e:  # 한 검색이 실패해도 나머지는 계속
            log(f"'{label}' 검색 실패: {e}")
            continue
        # 실제 제목에 키워드가 (모두) 들어간 기사만 남김
        items = [i for i in items if all(k.lower() in i["title"].lower() for k in group)]
        if config.get("skip_already_notified", True):
            items = [i for i in items if i["link"] not in seen]
        items.sort(key=lambda i: i["published"] or datetime.min.astimezone(), reverse=True)
        items = items[: config.get("max_items_per_keyword", 20)]
        if items:
            results[label] = items
    return results


def write_report(results):
    sections = []
    for keyword, items in results.items():
        rows = "".join(
            '<li><a href="{link}" target="_blank">{title}</a>'
            ' <span class="meta">{source} {time}</span></li>'.format(
                link=html.escape(i["link"]),
                title=html.escape(i["title"]),
                source=html.escape(i["source"]),
                time=i["published"].strftime("%m-%d %H:%M") if i["published"] else "",
            )
            for i in items
        )
        sections.append(f"<h2>{html.escape(keyword)} ({len(items)})</h2><ul>{rows}</ul>")
    page = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>뉴스 키워드 알림</title>
<style>
body {{ font-family: "Malgun Gothic", sans-serif; max-width: 860px; margin: 24px auto; padding: 0 16px; }}
li {{ margin: 6px 0; }} .meta {{ color: #888; font-size: 0.85em; }}
</style></head><body>
<h1>뉴스 키워드 알림 <small class="meta">{datetime.now():%Y-%m-%d %H:%M}</small></h1>
{"".join(sections)}
</body></html>"""
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(page)


def notify(title, message):
    try:
        from plyer import notification

        # Windows 토스트는 본문 256자 제한
        notification.notify(title=title, message=message[:250], app_name="뉴스 알림", timeout=15)
    except Exception as e:
        log(f"PC 알림 표시 실패 (pip install plyer 확인): {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="알림 표시 테스트")
    args = parser.parse_args()

    config = load_json(CONFIG_PATH, None)
    if not config or not config.get("keywords"):
        log("config.json 에 keywords 를 입력하세요.")
        return 1

    seen = set(load_json(SEEN_PATH, []))
    results = collect(config, seen)
    total = sum(len(items) for items in results.values())
    log(f"키워드 {config['keywords']} ({config.get('match', 'all')}) → 새 기사 {total}건")

    if total == 0:
        if args.test:
            notify("뉴스 알림 테스트", "알림이 정상적으로 표시됩니다. (새 기사 없음)")
        return 0

    write_report(results)
    # 여러 키워드에 걸린 같은 기사는 알림창에 한 번만 표시
    titles = list(dict.fromkeys(i["title"] for items in results.values() for i in items))
    total = len(titles)
    limit = config.get("max_titles_in_popup", 5)
    message = "\n".join(titles[:limit])
    if total > limit:
        message += f"\n…외 {total - limit}건"
    notify(f"뉴스 키워드 알림 {total}건", message)

    if config.get("open_report_in_browser", True):
        webbrowser.open(Path(REPORT_PATH).as_uri())

    # 오래된 기록이 끝없이 쌓이지 않도록 최근 2000개만 유지
    seen_list = list(seen) + [i["link"] for items in results.values() for i in items]
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen_list[-2000:], f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
