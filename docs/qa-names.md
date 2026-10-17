# BA-001／002 名稱來源與驗收

查核日期：2026-10-18。保留原名稱、stableId 與版次不變；只補可核對名稱與別名。`data/overrides.json` 是可重建的唯一人工來源，每個名稱記錄性質、來源及查核日期。

本機大多數譯文 PDF 是影像頁，無可提取的中文標題，未由英文檔名自行發明中文名。以下平台名稱僅表示平台實際繁中顯示名，沒有假定等於出版社正式商品名。

| 原文 | 中文名稱 | 性質及來源 |
| --- | --- | --- |
| A Feast for Odin | 奧丁的盛宴 | [BGA 繁中平台顯示名](https://zh.boardgamearena.com/gamepanel?game=feastforodin) |
| Lost Ruins of Arnak | 阿納克遺跡 | [BGA 繁中平台顯示名](https://zh.boardgamearena.com/gamepanel?game=arnak) |
| Space Base | 太空基地 | [BGA 繁中平台顯示名](https://zh.boardgamearena.com/gamepanel?game=spacebase) |
| Tapestry | 文明繪卷 | [BGA 繁中平台顯示名](https://zh.boardgamearena.com/gamepanel?game=tapestry) |
| Orléans | 奧爾良 | [繁中出版商新天鵝堡商品名](https://www.swanpanasia.com/products/orleans) |
| Excalibur | 王者之劍 | `翻譯好的規則書/Excalibur/Excalibur_Rulebook_CHT.pdf` 第 1 頁正文，屬本機規則書譯名，未查證出版商品名 |

BA-002 已補 12 款原清單遊戲的實際可驗收別名：AFFO、Manhattan Project、Energy Empire、Inventions、Trickerion、Avalon、Chicago 1875／CotBS、Rawr ’n Write／Rawr n Write、Voynich、Moonsaga、Orleans、Brass Birmingham。AFFO 是 BGA 明示縮寫，其餘來自現有規則書檔名或資料夾短名，來源逐筆列於 `aliasSources`。不把文件版號或 `.pdf` 當成遊戲名。相同原名的另一資料集主遊戲同時套用；擴充、新版不同名稱未自動套用主遊戲中文名。

驗收：`python3 scripts/build.py`（重建及 preflight）；`python3 tests/test_name_overrides.py` 驗證 6 款中文名、至少 10 款別名、來源檔案存在、來源性質完整、重建後名稱欄位留在可搜尋清單。網站可搜尋「奧丁的盛宴」「阿納克遺跡」「王者之劍」「AFFO」「CotBS」「Moonsaga」。實際瀏覽器搜尋整合由主流程驗收。
