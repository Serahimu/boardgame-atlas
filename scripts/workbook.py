"""Name-based XLSX reader (standard library); no worksheet/column positions assumed."""
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET
from zipfile import ZipFile
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
HEADERS = ['BGG 英文名稱','BGG 遊戲頁 URL','遊戲年份','玩家平均評分（BGG）','玩家人數','Type','Category','Mechanism','遊玩時間','重度（0–5）','封面圖庫 URL（BGG）','設計師','美術設計','出版社（第一家）','BGG 標示的集資平台','採用版次 Release Date','採用版次／語言','版次來源 URL','項目類型','主遊戲桌遊','遊戲類型（中文）','分類（中文）','遊戲機制（中文）','規則書等文件下載連結清單','文件查找結果','優先文件下載入口','原清單序號','BGG ID','收錄來源','官網／集資查找頁','查核日期','資料備註','主遊戲 BGG ID']

def read_workbook(path):
    with ZipFile(path) as z:
        strings = [''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
        targets = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        result = {}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet', NS):
            target = targets[sheet.get('{'+REL+'}id')]
            filename = target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl') / target)
            rows = []
            for row in ET.fromstring(z.read(filename)).findall('m:sheetData/m:row', NS):
                values = {}
                for cell in row:
                    column = cell.get('r').rstrip('0123456789')
                    value = cell.findtext('m:v', default='', namespaces=NS)
                    if cell.get('t') == 's': value = strings[int(value)]
                    elif cell.get('t') == 'inlineStr': value = ''.join(cell.find('m:is', NS).itertext())
                    values[column] = value
                rows.append(values)
            result[sheet.get('name')] = rows
        return result

def named_rows(rows, required):
    header_index = next((i for i, r in enumerate(rows) if set(required) <= set(r.values())), None)
    if header_index is None:
        raise ValueError('Missing required workbook columns: ' + ', '.join(required))
    header = rows[header_index]
    return [{header[c]: value for c, value in row.items() if header.get(c)} for row in rows[header_index+1:] if any(row.values())]

def game_rows(path, essen=False):
    books = read_workbook(path)
    if 'BGG完整清單' not in books: raise ValueError('Missing worksheet: BGG完整清單')
    headers = HEADERS if essen else HEADERS[:23]
    return named_rows(books['BGG完整清單'], headers)
