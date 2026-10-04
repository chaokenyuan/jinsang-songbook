"""抓取台灣點歌王（song.corp.com.tw）金嗓完整歌單，輸出 docs/data/songs.json 與 data/songs.csv。

資料來源 API 以 seq 分頁：每次回傳最多 50 筆，下一頁的 minId 帶上一頁最後一筆的 seq。
語言 × 歌名字數（Len 1~11，11 = 十字以上）兩層迴圈即可涵蓋全部歌曲。
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://song.corp.com.tw/api/song.aspx"
COMPANY = "金嗓"
LANGS = ["台", "國", "日", "客", "粵", "英", "山", "兒"]
PAGE_SIZE = 50
# 新抓的筆數少於上次的這個比例就視為抓取異常，不覆蓋舊資料
MIN_RATIO = 0.95

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "docs", "data", "songs.json")
CSV_PATH = os.path.join(ROOT, "data", "songs.csv")


def fetch(lang, length, min_id):
    query = dict(company=COMPANY, cusType="", minId=min_id, oid="", lang=lang, board="",
                 keyword="", singer="", sex="", Len=length, songDate="")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(query),
                                 headers={"User-Agent": "Mozilla/5.0"})
    last_error = None
    for attempt in range(5):
        try:
            body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
            return json.loads(body or "[]")
        except Exception as e:  # 網路抖動時重試
            last_error = e
            time.sleep(3 * (attempt + 1))
    raise last_error


def crawl():
    songs = {}
    for lang in LANGS:
        for length in range(1, 12):
            min_id, count = 0, 0
            while True:
                page = fetch(lang, length, min_id)
                if not page:
                    break
                for s in page:
                    songs[s["id"]] = s
                count += len(page)
                next_id = page[-1]["seq"]
                if next_id == min_id or len(page) < PAGE_SIZE:
                    break
                min_id = next_id
                time.sleep(0.2)
            print(f"{lang} Len={length}: {count}", flush=True)
    return list(songs.values())


def main():
    songs = crawl()
    previous, old = 0, None
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, encoding="utf-8") as f:
            old = json.load(f)
            previous = len(old["songs"])
    print(f"total={len(songs)} previous={previous}")
    if previous and len(songs) < previous * MIN_RATIO:
        sys.exit(f"抓到 {len(songs)} 筆，低於上次 {previous} 筆的 {MIN_RATIO:.0%}，判定異常不覆蓋")

    songs.sort(key=lambda s: (LANGS.index(s["lang"]) if s["lang"] in LANGS else 99, s["code"], s["id"]))

    # 網頁用精簡陣列格式，欄位順序見 fields
    fields = ["code", "name", "singer", "lang", "sex", "songDate", "counter", "youtubeID"]
    rows = [[s.get(k, "") for k in fields] for s in songs]
    # 歌單沒變就沿用舊的更新時間，避免每天只因時間戳而提交一個 5MB 檔
    if old and old.get("fields") == fields and old["songs"] == rows:
        updated = old["updated"]
    else:
        updated = time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 8 * 3600))
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"fields": fields, "updated": updated, "songs": rows},
                  f, ensure_ascii=False, separators=(",", ":"))

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    cols = ["code", "name", "singer", "lang", "sex", "len", "songDate", "counter", "subname",
            "albumName", "albumDate", "youtubeID", "id", "songDetailID"]
    headers = ["歌號", "歌名", "歌手", "語言", "性別", "字數", "上架年月", "點播數", "副標",
               "專輯", "專輯日期", "YouTube", "id", "songDetailID"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(headers)
        for s in songs:
            w.writerow([s.get(c, "") for c in cols])


if __name__ == "__main__":
    main()
