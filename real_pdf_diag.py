import sys
from pathlib import Path
sys.path.insert(0, r'C:\Projects\HealthTrajectory\backend')
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.report_parser import parse_report_pages, parsed_features_to_measurements
from app.services.feature_dictionary import validate_basic_features

pdf = Path(r'C:\Users\CHARITHPENDYALA\OneDrive\Documents\or.pdf')
result = extract_text_from_pdf(pdf)
print('extraction_success=', result.extraction_success)
print('page_count=', result.page_count)
print('extraction_method=', result.extraction_method)
print('warnings=', result.warnings)
print('page_count_actual=', len(result.pages))

pages = [{'page_number': p.page_number, 'text': p.text} for p in result.pages]
parsed = parse_report_pages(pages, extraction_method=result.extraction_method)
print('PARSED_FEATURES')
for f in parsed.features:
    print(f"{f.canonical_name}: value={f.value} unit={f.unit} page={f.source_page} source={f.source_text}")
print('PARSE_WARNINGS', parsed.warnings)
validation = validate_basic_features(parsed_features_to_measurements(parsed.features))
print('VALIDATION')
print('eligible_for_basic_model=', validation.eligible_for_basic_model)
print('missing_required_features=', validation.missing_required_features)
print('available_features=', validation.available_features)
print('invalid_features=', [(i.name, i.canonical_name, i.reason) for i in validation.invalid_features])
print('normalized=', [(n.canonical_name, str(n.value), n.unit) for n in validation.normalized_features])
