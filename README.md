# 金嗓找歌

每天自動從台灣點歌王（song.corp.com.tw）抓金嗓完整歌單，並提供網頁用歌手、歌名找歌。

- 網頁：`docs/index.html`（GitHub Pages，main 分支 `/docs`）
- 抓取：`python3 scripts/crawl.py`，輸出 `docs/data/songs.json`（網頁用）與 `data/songs.csv`（Excel 用）
- 排程：`.github/workflows/update.yml`，台灣時間每天 06:00；也可在 Actions 頁手動執行
- 防呆：新抓筆數少於上次 95% 視為異常，不覆蓋舊資料
