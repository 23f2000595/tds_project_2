import re

# Read the current file
with open('data_processor.py', 'r') as f:
    content = f.read()

# Find the section to replace (from 'cutoff' search to the fallback return)
start_pattern = r"if 'cutoff' in question_lower:"
end_pattern = r"notes: 'Using known cutoff value as fallback'"

# Find the start and end positions
start_match = re.search(start_pattern, content)
if start_match:
    start_pos = start_match.start()
    
    # Find the end of the section we want to replace
    # Look for the fallback return statement
    fallback_pattern = r"return \{[^{]*'answer': 33644,[^}]*'Using known cutoff value as fallback'[^}]*\}"
    end_match = re.search(fallback_pattern, content[start_pos:])
    
    if end_match:
        end_pos = start_pos + end_match.end()
        
        # The improved CSV processing code
        improved_code = '''            # Parse CSV and calculate sum of all numbers
            total_sum = 0
            for row in rows:
                for cell in row:
                    # Extract numbers from each cell
                    numbers = re.findall(r'-?\\d+\\.?\\d*', str(cell))
                    for num in numbers:
                        try:
                            total_sum += float(num)
                        except ValueError:
                            pass
            
            logger.info(f"Calculated sum from CSV: {total_sum}")
            
            return {
                'status': 'processed',
                'task_type': 'csv_processing',
                'answer': total_sum,
                'method': 'sum_calculation',
                'notes': f'Sum of all numbers in CSV: {total_sum}'
            }'''
        
        # Replace the section
        new_content = content[:start_pos] + improved_code + content[end_pos:]
        
        # Write the updated content
        with open('data_processor.py', 'w') as f:
            f.write(new_content)
        
        print("SUCCESS: CSV processing logic updated")
        print("The code now calculates the actual sum of numbers in the CSV file")
    else:
        print("ERROR: Could not find the end of the CSV processing section")
else:
    print("ERROR: Could not find the CSV processing section")

