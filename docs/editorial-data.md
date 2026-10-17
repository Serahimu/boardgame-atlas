# 人工查證資料

`data/editorial.json` 不包含私人 PDF 或推測內容。`games` 以穩定項目 ID 為 key，沒有對應資料時介面顯示「尚未查證／未登錄」。同名遊戲不自動配對。`mechanisms` 以來源中文機制名稱為 key。

每款可登錄以下欄位：

- `translations`: `{title,scope,status,edition,public,url,originalUrl,sourceDate,translatedDate,proofreadDate,changes:[{date,pages,text}]}`。scope 為主遊戲、擴充或輔助卡；status 為待翻譯、翻譯中、待校對或已完成。只有 public 嚴格為 true 才呈現譯文網址；發布前仍須確認授權。私人檔案不要把路徑或網址寫入公開檔案。
- `editionDifference` / `requirements`: `{text,source}`。未查證不填。
- `glossary`, `teaching`, `setup`, `faq`: `[{term,title,text,pages,source}]`。FAQ 的 title 應標示官方勘誤、常見問題或個人提醒。規則摘要需要可追溯頁碼。
- 機制：`mechanisms[名稱] = {description,source}`。缺解釋時仍可瀏覽資料收錄範例。

BA-058 AI 規則問答依規劃 10.4 留在遠期，沒有外部服務、文件檢索或可驗證來源頁碼前不提供生成答案。

翻譯檔檢查目前驗證登錄格式與完成狀態，不會將沒有清冊的項目誤判為缺檔。失效 URL 必須透過獨立連結查核工具檢查；瀏覽器不能可靠地跨站驗證所有 PDF。私人本機檔不掃描、不上傳。

驗收：`node --test tests/enhancements.test.cjs`，涵蓋 HTML escaping、安全連結、缺值、穩定 ID、沒有來源時保持空白，以及去重不混淆語言／版次。

## 私人本機檔對應檢查

執行 `python3 scripts/audit_translations.py`，遞迴掃描專案上兩層的輸入與翻譯資料夾。可用 `--input`、`--translated` 指定目錄；報告只能輸出至 Git 忽略的 `.private/`。以原檔名對應 `_CHT.pdf`，不做模糊名稱猜測；列出缺檔、多個候選與新增未對應譯文。不讀取或上傳 PDF 內容。

預設不改公開資料。人工核對遊戲與版次後，於 `.private/confirmed-map.json` 建立 `[{"confirmed":true,"sourceName":"原檔名.pdf","stableId":"已核對ID","scope":"主遊戲","edition":"已查證版次"}]`，再以 `--confirmed-map .private/confirmed-map.json` 更新公開狀態。只存無私人路徑的狀態；檔案存在不代表翻譯已校對，因此預設待校對。

測試：`python3 -m unittest discover -s tests -p 'test_translation_audit.py'`。
