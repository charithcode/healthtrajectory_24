import sys
from pathlib import Path
sys.path.insert(0, r'C:\Projects\HealthTrajectory\backend')
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.report_parser import parse_report_pages

pdf = Path(r'C:\Users\CHARITHPENDYALA\OneDrive\Documents\or.pdf')
result = extract_text_from_pdf(pdf)
print('extraction_success=', result.extraction_success)
print('page_count=', result.page_count)
print('extraction_method=', result.extraction_method)
print('warnings=', result.warnings)
print('total_pages=', len(result.pages))
for page in result.pages[:5]:
    print('--- PAGE', page.page_number, '---')
    print(page.text[:1500])

pages = [{'page_number': p.page_number, 'text': p.text} for p in result.pages]
parsed = parse_report_pages(pages, extraction_method=result.extraction_method)
print('parsed_features=', [(f.canonical_name, str(f.value), f.source_page, f.unit) for f in parsed.features])
print('parse_warnings=', parsed.warnings)
