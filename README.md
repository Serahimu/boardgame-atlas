# 桌遊藏書室 · Boardgame Atlas

以繁體中文瀏覽桌遊資料的靜態網站，透過 GitHub Pages 部署。頁面提供搜尋、篩選、格狀／列表檢視，以及主遊戲、擴充、Promo、新版與相關文件的探索入口。

功能與優化提案見[產品規劃文件](docs/plans/product-roadmap.md)，包含 108 項建議、優先級、交付階段、資料依賴與驗收方向；實際交付、來源內容覆蓋及遠期服務邊界見[實作追蹤](docs/implementation-status.md)與[驗收紀錄](docs/acceptance.md)。

## 三份清單

| 分頁 | 入口 | 資料範圍 |
| --- | --- | --- |
| AI 翻譯規則書清單 | [`index.html`](index.html) | 現有翻譯規則書收藏的桌遊資料：120 款主遊戲、共 170 個項目 |
| Essen 2026 Most Wanted | [`essen.html`](essen.html) | 1,745 款主遊戲、1,131 個擴充、488 個 Promo、299 個新版、3 個佔位項目，共 3,666 個項目 |

| 2026 New Games | [`newgames.html`](newgames.html) | BGG SPIEL Essen 2026 官方預覽清單：1,406 筆展會項目、1,286 個 BGG ID，保留語言與版次 |

頁首導覽使用一般相對連結切換三個 HTML 頁面，各自都有可分享的網址；重新整理、上一頁／下一頁及 GitHub Pages 專案子路徑皆不需要額外的路由設定。三頁共用 `app.js` 與 `styles.css`。

Essen 資料查核日期為 **2026-10-17**，包含 1,296 筆原始清單對照、3,102 筆關聯、20,719 份文件及 31 筆整理說明。此網站呈現來源資料的快照，不會即時向 BGG 查詢。

## 使用方式

- 搜尋遊戲、相關項目、設計師或機制；按 `/` 可聚焦搜尋框。
- 依玩家人數、遊玩時間、重度、評分及相關內容篩選。時間採上限；套用數值條件時會排除缺值項目。
- 機制、類型、分類可複選：同組任一項符合即可，不同組須同時符合。
- 兩頁皆以主遊戲為目錄入口，每頁可選 24／48／96 款，可排序或切換格狀／列表。檢視方式會儲存在瀏覽器；切換清單後搜尋與篩選會重新開始。
- 點擊卡片查看詳情，繼續探索相關項目；按 Esc 或關閉按鈕離開詳情。
- 兩個分頁都可切換「桌遊清單／出版社清單／設計師清單」。出版社卡片顯示 BGG 圖片、名稱、主遊戲數與收錄項目數，點選後可瀏覽該出版社在**目前清單**中的主遊戲、擴充、Promo 與新版，再點遊戲開啟原有詳情頁。
- 出版社目錄可依出版社或收錄遊戲名稱搜尋，依名稱／收錄數排序，並支援分頁及格狀／列表。進入出版社後可依項目類型與其他遊戲條件篩選；返回目錄會保留出版社搜尋、排序與頁碼。
- `index.html#publishers`、`essen.html#publishers` 可直接開啟出版社清單；`#publisher=<BGG 出版社 ID>` 可分享某家出版社的收錄項目。瀏覽器上一頁／下一頁及重新整理均支援。切換兩個分頁時會保留出版社瀏覽模式。
- Essen 預設按原清單順序排列，補入的關聯主遊戲排在有來源序號的遊戲之後。「相關內容 → 佔位項目」可查看原始清單的 3 筆非具名項目。
- Essen 詳情包含所有關聯遊戲、資料來源、原清單對照與文件。文件可搜尋名稱、類別或語言；「資料範圍與整理說明」可展開查看工作簿說明或下載完整 Excel。

### 設計師視角

兩頁的「設計師清單」依目前清單的來源署名建立，分別收錄132位與1,445位設計師。共同設計作品分別歸入每位設計師，缺少署名及佔位項目不加入人物目錄。姓名依來源分組；沒有推測不同寫法為同一人，也未把同名者視為已查證的同一人物。

可依設計師或作品名稱搜尋、按姓名／收錄數排序、分頁及切換格狀／列表。進入設計師後可查看主遊戲、擴充、Promo與新版，沿用篩選、詳情及名稱複製。`index.html#designers`、`essen.html#designers`直接開啟目錄，`#designer=uwe%20rosenberg`可定位設計師作品；兩分頁切換時保留設計師視角。

設計師清單卡片與作品頁顯示經 BGG 遊戲署名核對的人物圖片，並可開啟人物頁及照片來源。兩份來源 Excel 的「設計師資料」工作表保存人物 ID、照片網址、本地圖片路徑、核對遊戲、日期與缺圖原因；原有遊戲及文件工作表保持不變。BGG 尚無主要圖片或人物無法確認時保留姓名縮寫，不使用其他人物的圖片。

### 更新設計師照片

```bash
python3 scripts/fetch_designers.py
python3 scripts/fetch_designer_galleries.py --apply-reviewed
```

這是需網路、`Pillow` 與 `requests` 的獨立查核工作，使用限速請求並保存可接續的遊戲署名與人物圖片快取；`--retry-errors` 重試暫時失敗的請求。僅採用對應遊戲署名中完全相符且無衝突的人物連結，再核對人物頁 ID 與姓名，下載 BGG 主要圖片至 `assets/designers/`，排除通用缺圖圖示及已視覺確認的非人物圖片。

圖庫查核預設只保存來源及照片說明；`--apply-reviewed` 僅下載腳本明列且已核對說明、目視確認的圖片，不任選圖庫第一張。新圖庫照片須先核對並加入選取表。2026-10-18 查核共取得 **912 張設計師圖片**，其中27張補自圖庫；另外599位沒有可確認圖片、1位存在同名人物衝突。沒有主要照片的626個人物圖庫均已查核，缺圖原因與來源保存在 Excel。

使用本機 Codex 提供的 Artifact Tool 環境執行 `python3 scripts/update_designer_workbooks.py`，會將查核快取寫入兩份 Excel 的「設計師資料」，保留原有工作表內容；也可直接維護該工作表。之後 `python3 scripts/build.py` 會離線產生 `data/designers.json`。一般建置與網站瀏覽不會重新向 BGG 查詢。

## 專案結構

```text
.
├── index.html                          # 原有清單，共用模板產生，資料與圖片外置
├── essen.html                          # Essen 分頁
├── app.js                              # 共用搜尋、篩選、分頁與詳情邏輯
├── styles.css                          # 共用樣式與響應式版面
├── assets/covers/                      # 網站本地 WebP 封面，依 BGG ID 命名
├── assets/publishers/                  # 從 BGG 下載的出版社圖片
├── data/
│   ├── essen.json                      # Essen 全部項目、關聯與來源對照
│   ├── essen-notes.json                # 工作簿「整理說明」
│   ├── cover-manifest.json             # 封面圖片、BGG ID、來源與查核記錄
│   ├── publishers.json                 # 出版社 ID、圖片來源及原始名稱對應
│   ├── publisher-game-links.json       # BGG 遊戲 → 出版社關聯查核快取
│   └── essen-documents/0.json … 31.json # 依 BGG ID 分組的文件資料
├── scripts/build_essen.py              # Excel → 靜態 JSON 轉換程式
├── scripts/fetch_covers.py             # 下載並驗證 BGG 主要圖片，可接續進度
├── scripts/build_publishers.py         # 建立出版社對應與下載圖片，可接續進度
├── BGG桌遊資料_完整.xlsx                 # 原有收藏資料來源
├── Essen2026_Most_Wanted_桌遊資料_完整.xlsx # Essen 資料來源
└── SPIEL_2026_桌遊清單.xlsx              # 原始展會清單參考
```

訪客不需要套件、帳號或 API 金鑰。瀏覽器直接讀取靜態 HTML、CSS、JavaScript 與 JSON；維護者用 Python 3 重建，發布前以 Node.js 檢查語法及執行回歸測試。Essen 文件按 BGG ID 的餘數分為 32 份，在開啟有文件的項目詳情時才載入對應檔案，並於同次頁面瀏覽中快取。

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

原有清單亦從 `BGG桌遊資料_完整.xlsx` 由統一建置流程產生 `data/catalog.json`，不再內嵌於 HTML。修改來源後執行 `python3 scripts/build.py`。

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

### 更新出版社

```bash
python3 scripts/build_publishers.py
```

使用與封面下載相同的 `Pillow`、`requests` 環境。程式讀取兩份清單的出版社欄位，從 BGG 遊戲資料的出版社關聯核對公司 ID，再下載該公司的主要圖片至 `assets/publishers/`。主要圖片未設定時，會再查該公司圖庫中明確標為 Logo 的圖片。快取會保留，重跑僅補充新的資料或失敗項目；`--limit 12` 可少量試跑，`--retry-missing` 可重新查找缺圖出版社。

分類依資料收錄的出版社欄位（通常為第一家），不擴充為 BGG 列出的所有地區出版商。欄位內明列多家出版社者分別歸類，含逗號的單一公司名稱則保留完整。已確認的別名與來源錯置集中在腳本的名稱對應表；例如 Solar Sphere 原欄位誤填設計師，依 BGG 遊戲 329228 歸入 Dranda Games。原清單的 Worms: The Board Game 另已修正為正確遊戲 ID 397788 與對應封面。

出版社圖片依 BGG 公司 ID 儲存與核對；沒有圖片或無法確認身分時會顯示明確替代文字，不借用別家出版社圖片。未提供出版社與自行出版等來源分類仍可瀏覽。更新後請一併提交腳本、`publishers.json`、關聯快取及新增的出版社圖片。

目前兩份清單合計 700 個出版社／來源分類，取得 659 份 BGG 圖片，另外 40 家 BGG 未提供可確認的主要圖片或 Logo，1 類為出版社資料未提供。各分頁會依自身收錄項目建立目錄，不顯示另一份清單才有的出版社。

## GitHub Pages 部署

此專案以 `dev` 分支的 `/docs` 發布網站。執行 `python3 scripts/publish_pages.py` 先完成建置與檢查，再把公開白名單輸出到 `docs/`；來源 Excel、品質報告與私人資料不加入網站發布包。若使用分支部署，在 GitHub 的 **Settings → Pages** 選擇 **Deploy from a branch → dev → /docs**；若已配置其他部署流程，需一併發布兩個 HTML、共用資源、完整 `data/` 與 `assets/` 目錄。

推送至部署分支後，等待 GitHub Pages 部署完成，再檢查首頁與 `essen.html`。所有站內資源皆使用相對路徑，適用於 `https://<帳號>.github.io/boardgame-atlas/` 形式的專案網站。`Validate static catalog` Actions 在 `dev` 推送與 PR 執行自動檢查；本機 pre-push hook 亦檢查資料與測試。

## 驗證

提交前可執行：

```bash
python3 scripts/build_essen.py
node --test tests/*.test.cjs  # 發布前需要 Node.js
git diff --check
```

再以本機 HTTP 預覽兩個分頁，檢查搜尋、數值與多選篩選、排序、下一頁、格狀／列表、空結果重設、關聯遊戲及文件搜尋。修改版面時亦應確認手機寬度沒有水平溢出。

## 資料與權利

桌遊資料與文件入口依工作簿所列 BGG／官方來源呈現。遊戲封面與規則文件的權利屬於各權利人。外部文件入口不代表網站提供直接下載或翻譯檔案；部分來源需要登入，連結、語言標示、評分、發行資訊也可能隨時間變更。來源語言與檔名辨識語言會分別保留，以便核對原檔。

## 統一資料建置與檢查

Python 3 標準函式庫即可離線重建兩份清單；發布前 JavaScript 語法檢查另需要 Node.js：

```bash
python3 scripts/build.py
python3 -m unittest discover -s tests -p 'test_data_model.py'
python3 scripts/data_reports.py quality
python3 scripts/data_reports.py diff --baseline HEAD
python3 scripts/audit_resources.py
```

`data/datasets.json` 定義來源、資料集識別碼、年份及來源快照日期。原清單從 Excel 依工作表與欄名讀取；`data/catalog-cover-manifest.json` 保存外置封面對應。人物、標籤、數值與發行日期有結構化欄位，來源字串仍保留。資料列重排不改變 `stableId`；`data/id-migrations.json` 保留原數字 ID 遷移，`entityId` 用於跨清單比對相同項目及版次。

`templates/site.html` 與 `templates/pages.json` 共用兩頁結構與內容設定。重建保留現有頁面的 CSS／JavaScript 接線；修改頁面共同結構請編輯模板。清單載入 `data/catalog.json` 或 `data/essen.json`，詳情依每筆 `detailPath` 按需取得，以 `stableId` 為分片記錄鍵；文件沿用獨立分片。

人工修正放在 `data/overrides.json`，每筆須提供 `reason`、`source` 與 `fields`。以穩定 ID 為鍵可新增 `nameZh`、`aliases`、出版社或封面修正；不得覆寫身份及關聯欄位。來源更新後會重新套用。

報告位於 `data/reports/`。品質與資源盤點只報告問題，不刪除檔案；來源缺值不會補成猜測資料。連結查核預設只盤點並標示未查核，使用下列指令才會連線，並限制數量及每次間隔：

```bash
python3 scripts/check_links.py --check --limit 20 --interval 1
```

`401` 或導向登入頁記為需登入，`403` 記為存取受限，`404/410` 記為失效，`429/5xx` 與連線失敗記為暫時不可用，保留查核日期。這項工作不在一般建置中執行；補圖也只在明確指定 `--fetch-covers` 時執行。

`python3 scripts/build.py --dist` 另外產生明確白名單的公開網站包，包含更新頁、遊戲／文件資料和圖片，排除來源 Excel、開發腳本、品質報告與本機私人檔案。此包會移除 Excel 下載入口。平常的根目錄輸出保留 Excel 下載，供 `dev` 根目錄的 GitHub Pages 部署使用。發布檢查會阻擋缺檔、JSON 錯誤、無效關聯、JavaScript 語法錯誤，以及未授權公開的翻譯 URL。

Pages 發布前執行 `python3 scripts/publish_pages.py`，將網站來源與產出的 `docs/` 一併提交至 `dev`。`docs/_config.yml` 排除規劃與驗收文件。

穩定 ID 由 `data/identity-registry.json` 持續保存，來源 BGG ID（缺值時使用正規化 URL）、項目類型與版次 URL 為優先識別鍵；遊戲名稱更正、BGG 網址 slug 或追蹤參數變動不改變已發佈的 ID。只有同來源／類型／版次存在多個項目時才以名稱消歧；這類項目更名時，建置會要求在 registry 的 `names` 加入已查證的新別名，避免錯接收藏。請提交並保留 registry，不要每次重建刪除它。歷史數字 ID 遷移也會保留最早對應，新增項目請使用穩定 ID 分享網址。

目前另提供收藏／私人備註／備份、比較與推薦、文件分類語言搜尋，以及裝置內原文譯文PDF閱讀。檔案只在瀏覽器內建立Blob入口，關閉或切換詳情即釋放，不上傳。中文名、版次差異和規則摘要只呈現有來源的已登錄內容。

### 2026 New Games

來源為 `Essen2026_GeekPreview_1406_桌遊資料_完整.xlsx`，由同一個 Essen 匯入器建置。`data/datasets.json` 設定分頁、清單、文件分片與整理說明；搜尋、篩選、詳情、出版社／設計師目錄、個人清單與逛展工具共用現有程式。

每個展會版次保留獨立穩定 ID 與原清單對照，合計固定 1,406 筆。可用「全部項目」查看所有展會項目；預設與 Most Wanted 一樣只顯示主遊戲。關聯主遊戲未收錄時保留名稱與 BGG ID，不另補入清單。設計師照片沿用既有工作簿已查證的共用目錄，新增姓名沒有照片時使用既有替代顯示。

2026-10-22 匯出展會資料；沿用基本資料與文件的原查核日期仍保留於詳情中。執行 `python3 scripts/publish_pages.py` 同步發布三個分頁。
