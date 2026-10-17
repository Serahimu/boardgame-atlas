# 桌遊藏書室 · Boardgame Atlas

以繁體中文瀏覽桌遊資料的靜態網站，透過 GitHub Pages 部署。頁面提供搜尋、篩選、格狀／列表檢視，以及主遊戲、擴充、Promo、新版與相關文件的探索入口。

## 兩份清單

| 分頁 | 入口 | 資料範圍 |
| --- | --- | --- |
| AI 翻譯規則書清單 | [`index.html`](index.html) | 現有翻譯規則書收藏的桌遊資料：120 款主遊戲、共 170 個項目 |
| Essen 2026 Most Wanted | [`essen.html`](essen.html) | 1,745 款主遊戲、1,131 個擴充、488 個 Promo、299 個新版、3 個佔位項目，共 3,666 個項目 |

頁首導覽使用一般相對連結切換兩個 HTML 頁面，各自都有可分享的網址；重新整理、上一頁／下一頁及 GitHub Pages 專案子路徑皆不需要額外的路由設定。兩頁共用 `app.js` 與 `styles.css`。

Essen 資料查核日期為 **2026-10-17**，包含 1,296 筆原始清單對照、3,102 筆關聯、20,719 份文件及 31 筆整理說明。此網站呈現來源資料的快照，不會即時向 BGG 查詢。

## 使用方式

- 搜尋遊戲、相關項目、設計師或機制；按 `/` 可聚焦搜尋框。
- 依玩家人數、遊玩時間、重度、評分及相關內容篩選。時間採上限；套用數值條件時會排除缺值項目。
- 機制、類型、分類可複選：同組任一項符合即可，不同組須同時符合。
- 兩頁皆以主遊戲為目錄入口，每頁 48 款，可排序或切換格狀／列表。檢視方式會儲存在瀏覽器；切換清單後搜尋與篩選會重新開始。
- 點擊卡片查看詳情，繼續探索相關項目；按 Esc 或關閉按鈕離開詳情。
- Essen 預設按原清單順序排列，補入的關聯主遊戲排在有來源序號的遊戲之後。「相關內容 → 佔位項目」可查看原始清單的 3 筆非具名項目。
- Essen 詳情包含所有關聯遊戲、資料來源、原清單對照與文件。文件可搜尋名稱、類別或語言；「資料範圍與整理說明」可展開查看工作簿說明或下載完整 Excel。

## 專案結構

```text
.
├── index.html                          # 原有清單，內嵌原有 JSON 與封面
├── essen.html                          # Essen 分頁
├── app.js                              # 共用搜尋、篩選、分頁與詳情邏輯
├── styles.css                          # 共用樣式與響應式版面
├── assets/covers/                      # 網站本地 WebP 封面，依 BGG ID 命名
├── data/
│   ├── essen.json                      # Essen 全部項目、關聯與來源對照
│   ├── essen-notes.json                # 工作簿「整理說明」
│   ├── cover-manifest.json             # 封面圖片、BGG ID、來源與查核記錄
│   └── essen-documents/0.json … 31.json # 依 BGG ID 分組的文件資料
├── scripts/build_essen.py              # Excel → 靜態 JSON 轉換程式
├── scripts/fetch_covers.py             # 下載並驗證 BGG 主要圖片，可接續進度
├── BGG桌遊資料_完整.xlsx                 # 原有收藏資料來源
├── Essen2026_Most_Wanted_桌遊資料_完整.xlsx # Essen 資料來源
└── SPIEL_2026_桌遊清單.xlsx              # 原始展會清單參考
```

不需要 Node.js、套件安裝、API 金鑰或網站建置流程。瀏覽器直接讀取 HTML、CSS、JavaScript 與 JSON。Essen 文件按 BGG ID 的餘數分為 32 份，在開啟有文件的項目詳情時才載入對應檔案，並於同次頁面瀏覽中快取。

## 本機預覽

需要 Python 3。在專案根目錄執行：

```bash
python3 -m http.server 8000
```

開啟 [原有清單](http://localhost:8000/index.html) 或 [Essen 分頁](http://localhost:8000/essen.html)。Essen 透過 `fetch` 載入 JSON，請使用 HTTP 預覽，避免直接以 `file://` 開啟。

## 更新 Essen 資料

1. 更新根目錄的 `Essen2026_Most_Wanted_桌遊資料_完整.xlsx`。
2. 保留目前的五張工作表順序、欄位順序，以及第 5 列標題、第 6 列開始的資料配置。
3. 執行轉換程式：

   ```bash
   python3 scripts/build_essen.py
   ```

4. 確認輸出的項目、文件、關聯與原清單筆數符合新版工作簿，並預覽搜尋、篩選、分頁、詳情與文件。
5. 若新增遊戲，依下一節取得其封面並再次執行轉換。將工作簿、`data/` 與新增的 `assets/covers/` 一起 commit、push。若查核日期變動，同步修改 `essen.html` 側欄日期與本 README 的資料範圍。

轉換程式僅使用 Python 標準函式庫，不修改工作簿。它會讀取「BGG完整清單」「文件清單」「主遊戲關聯」「原清單對照」「整理說明」，並檢查文件與關聯的對應資料。Excel 內部導覽連結會轉換為網站的詳情／文件入口；原始工作簿仍可下載查閱。

同名遊戲可能具有不同 BGG ID，部分新版也可能與主遊戲共用 BGG ID。網站以工作簿資料列的獨立 ID 導覽，使用關聯表中的 BGG ID、名稱、類型來對應項目，並保留多對多與巢狀關聯。文件以 BGG ID 共用，因此不同版次詳情可能呈現相同的文件清單，不能直接加總每張詳情的文件數作為全站文件總數。

原有清單仍以 `index.html` 的 `game-data` 區塊為資料來源；修改 `BGG桌遊資料_完整.xlsx` 不會自動更新該區塊。

### 更新封面

Excel 的 K 欄「封面圖庫 URL（BGG）」是 `/images` 網頁，不能直接作為 `<img>` 的圖片來源。Essen 使用 `cover-manifest.json` 對應的本地 WebP 檔案，瀏覽時不必連線 BGG。圖片取自對應 BGG ID 的主要圖片；共用 BGG ID 的不同版次會共用該遊戲圖片。

僅在下載／更新封面時需要 Python 的 `Pillow` 與 `requests` 套件及網路連線：

```bash
python3 -m pip install Pillow requests
python3 scripts/fetch_covers.py
python3 scripts/build_essen.py
```

下載程式限制 BGG metadata 請求速率，核對回傳的遊戲 ID，解碼並壓縮圖片，每 25 個項目保存來源記錄。再次執行會跳過已下載圖片並重試失敗項目；`--limit 10` 可先試跑，`--retry-missing` 可重新查找來源尚無圖片的項目。

`cover-manifest.json` 保留原始圖片網址、來源 metadata 網址、圖片 ID、名稱、尺寸與日期。沒有 BGG ID 的 Wondrous Places 擴充使用出版商官方 Gamefound 商品圖，並以工作簿內的來源 URL 對應。BGG 缺圖的部分擴充與 Flipmas 版本另以出版商的 Gamefound、GameFlight、Kosmos 商品圖補足，記錄 `provider: publisher` 及原始品名供核對。

目前有 **3,314 個本地圖片檔**，對應 **3,587 個資料項目**，其中 **1,739 / 1,745 款主遊戲**有圖片。其餘 75 個具名項目的 BGG 主要圖片為通用缺圖圖示，且尚未補得可確認的封面，因此明確顯示「來源暫無封面」。其中主遊戲為 Aeris、Anou、Join the Resistance!、Qualified!、Secrets of the Lost Dungeon、High Frontier Lite；另外 3 筆原清單佔位項目本身不是具名桌遊。BGG 的通用藍色缺圖盒圖不當作封面發布，也不以其他遊戲的圖片補入。若本地圖片無法載入，頁面會顯示遊戲名稱與載入失敗說明。

## GitHub Pages 部署

此專案可直接以根目錄的靜態檔案部署。若使用分支部署，在 GitHub 的 **Settings → Pages** 選擇 **Deploy from a branch → main → / (root)**；若已配置其他部署流程，需一併發布兩個 HTML、共用資源、完整 `data/` 與 `assets/` 目錄。

推送至部署分支後，等待 GitHub Pages 部署完成，再檢查首頁與 `essen.html`。所有站內資源皆使用相對路徑，適用於 `https://<帳號>.github.io/boardgame-atlas/` 形式的專案網站。此儲存庫不包含額外的 Actions 工作流程。

## 驗證

提交前可執行：

```bash
python3 scripts/build_essen.py
node --check app.js  # 若本機已安裝 Node.js，可檢查 JavaScript 語法
git diff --check
```

再以本機 HTTP 預覽兩個分頁，檢查搜尋、數值與多選篩選、排序、下一頁、格狀／列表、空結果重設、關聯遊戲及文件搜尋。修改版面時亦應確認手機寬度沒有水平溢出。

## 資料與權利

桌遊資料與文件入口依工作簿所列 BGG／官方來源呈現。遊戲封面與規則文件的權利屬於各權利人。外部文件入口不代表網站提供直接下載或翻譯檔案；部分來源需要登入，連結、語言標示、評分、發行資訊也可能隨時間變更。來源語言與檔名辨識語言會分別保留，以便核對原檔。
