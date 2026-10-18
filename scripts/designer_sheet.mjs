// Run through update_designer_workbooks.py with the bundled Artifact Tool runtime.
import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const [payloadPath, mode = 'author'] = process.argv.slice(2);
const payload = JSON.parse(await fs.readFile(payloadPath, 'utf8'));
for (const job of payload.jobs) {
  if (mode === 'preview' || mode === 'verify') {
    const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(job.path));
    const preview = await workbook.render({ sheetName: mode === 'preview' ? 'BGG完整清單' : '設計師資料', range: mode === 'preview' ? 'A2:E8' : 'A1:E8', scale: 1.3, format: 'png' });
    const destination = mode === 'preview' ? job.previewBefore : job.previewAfter;
    await fs.writeFile(destination, new Uint8Array(await preview.arrayBuffer()));
    console.log(`Saved workbook preview: ${destination}`);
    continue;
  }
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add('設計師資料');
  sheet.showGridLines = false;
  const rows = [payload.headers, ...job.rows.map(row => row.map((value, i) => i === 9 && value ? new Date(`${value}T00:00:00Z`) : value))];
  sheet.getRange(`A1:O${rows.length}`).values = rows;
  sheet.getRange(`A1:O${rows.length}`).format = {
    font: { name: 'Arial', size: 10, color: '#202124' }, verticalAlignment: 'center', rowHeight: 22,
  };
  sheet.getRange('A1:O1').format = { fill: '#1F4E78', font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' }, rowHeight: 38, wrapText: true };
  const widths = [30, 32, 18, 30, 55, 60, 42, 18, 22, 16, 60, 55, 20, 60, 55];
  widths.forEach((width, index) => sheet.getRangeByIndexes(0, index, rows.length, 1).format.columnWidth = width);
  if (rows.length > 1) sheet.getRange(`J2:J${rows.length}`).setNumberFormat('yyyy-mm-dd');
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(1);
  workbook.recalculate();
  console.log((await workbook.inspect({ kind: 'table', range: '設計師資料!A1:E4', include: 'values,formulas', tableMaxRows: 4, tableMaxCols: 5, maxChars: 1600 })).ndjson);
  const errors = await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 10 }, maxChars: 1200 });
  console.log(errors.ndjson);
  const preview = await workbook.render({ sheetName: '設計師資料', range: 'A1:E8', scale: 1.2, format: 'png' });
  await fs.writeFile(job.previewAfter, new Uint8Array(await preview.arrayBuffer()));
  await (await SpreadsheetFile.exportXlsx(workbook)).save(job.authoredSheet);
  console.log(`Authored ${job.rows.length} designer records: ${job.authoredSheet}`);
}
