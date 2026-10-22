#!/usr/bin/env python3
"""Export an explicit public website allowlist; source workbooks/reports are excluded."""
import re
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC_FILES=['index.html','essen.html','updates.html','styles.css','personal.css','enhancements.css','app.js','catalog-core.js','personal.js','enhancements.js','updates.js','data/catalog.json','data/essen.json','data/essen-notes.json','data/publishers.json','data/designers.json','data/editorial.json','data/datasets.json','data/id-migrations.json','data/document-facets.json']
PUBLIC_DIRECTORIES=['assets','data/details','data/essen-documents']
def main():
    from dataset_config import configured_datasets
    from validate_site import main as validate
    validate()
    destination=ROOT/'dist'
    if destination.exists():shutil.rmtree(destination)
    destination.mkdir()
    files=list(PUBLIC_FILES)
    directories=list(PUBLIC_DIRECTORIES)
    for config in configured_datasets():
        files.extend([config['page'],config['listPath']])
        if config.get('notesPath'):files.append(config['notesPath'])
        if config.get('documentsPath'):directories.append(config['documentsPath'])
    for name in dict.fromkeys(files):
        source=ROOT/name
        if not source.is_file():raise ValueError('Missing public file: '+name)
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix=='.html':
            text=source.read_text()
            text=re.sub(r'<a\b[^>]*href="[^"]+\.xlsx"[^>]*>.*?</a>','完整 Excel 未包含於此發布包',text)
            target.write_text(text)
        else:shutil.copy2(source,target)
    for name in dict.fromkeys(directories):shutil.copytree(ROOT/name,destination/name)
    (destination/'.nojekyll').write_text('')
    if list(destination.rglob('*.xlsx')) or (destination/'data/reports').exists():raise ValueError('Unexpected private/source output')
    print(f'Exported {len(list(destination.rglob("*")))} public paths to dist/')
if __name__=='__main__':main()
