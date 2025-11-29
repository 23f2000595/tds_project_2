# This shows the exact fix needed in _process_csv_with_analysis function

print("CURRENT CODE (lines 199-203):")
print("if csv_url.startswith('/') and base_url:")
print("    csv_url = urljoin(base_url, csv_url)")
print("elif csv_url.startswith('/'):")
print("    csv_url = urljoin('https://tds-llm-analysis.s-anand.net', csv_url)")
print("")
print("ADD THIS AFTER line 203:")
print("elif not csv_url.startswith(('http://', 'https://')) and base_url:")
print("    csv_url = urljoin(base_url, csv_url)")
print("")
print("This will handle 'demo-audio-data.csv' by converting it to full URL")
