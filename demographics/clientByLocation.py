import sys
import csv
from io import StringIO
from datetime import datetime

def get_csv_data(csvPath):
    """
    Reads CSV data from file, handling common encodings.
    """
    try:
        # Try UTF-8 first (most common)
        with open(csvPath, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Fall back to Latin-1 (handles most special characters)
        with open(csvPath, 'r', encoding='latin-1') as file:
            return file.read()

def csv_to_dictionary(data):
    """
    Converts a CSV formatted string into a list of dictionaries.
    Args:
        data (str): A string containing CSV formatted data.
    Returns:
        list: A list of dictionaries where each dictionary represents a row in the CSV.
    """
    f = StringIO(data)
    reader = csv.DictReader(f)
    return [row for row in reader]

def process_client_by_location(data):
    """
    Processes client data to group by location and count unique patients in each location.
    Args:
        data (list): A list of dictionaries containing client information, where each dictionary
                     has 'Location' and 'Patient' keys.
    Returns:
        dict: A dictionary with locations as keys and the count of unique patients in each location as values.
    """
    location_patients = {}  # Dict of sets to track unique patients per location
    
    for row in data:
        location = row.get('Location')
        patient = row.get('Patient')
        
        # Skip rows without location or patient
        if not location or not location.strip() or not patient or not patient.strip():
            continue
            
        location = location.strip()
        patient = patient.strip()
        
        # Initialize set for this location if needed
        if location not in location_patients:
            location_patients[location] = set()
        
        # Add patient to the set (automatically handles duplicates)
        location_patients[location].add(patient)
    
    # Convert sets to counts
    location_count = {location: len(patients) for location, patients in location_patients.items()}
    
    return location_count

def generate_report(location_count, sort_by='location', output_prefix="location_report"):
    """
    Generates a formatted report of unique patient counts by location.
    Writes the output to both txt and csv files.
    Args:
        location_count (dict): Dictionary with locations as keys and counts as values
        sort_by (str): 'location' for alphabetical or 'count' for by count
        output_prefix (str): Prefix for output filenames
    Returns:
        str: Formatted report string
    """
    if not location_count:
        return "No client data found."
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = f"{output_prefix}_{timestamp}.txt"
    csv_filename = f"{output_prefix}_{timestamp}.csv"
    
    # Sort the data
    if sort_by == 'count':
        # Sort by count (descending), then by location name for ties
        sorted_items = sorted(location_count.items(), key=lambda x: (-x[1], x[0]))
    else:
        # Sort alphabetically by location
        sorted_items = sorted(location_count.items())
    
    # Build the report for console and txt file
    report = []
    report.append("\n" + "="*50)
    report.append("UNIQUE PATIENT COUNT BY LOCATION REPORT")
    report.append("="*50)
    report.append(f"{'Location':<30} {'Unique Patients':>15}")
    report.append("-"*50)
    
    # Prepare data for files
    txt_lines = []
    txt_lines.append("="*50)
    txt_lines.append("UNIQUE PATIENT COUNT BY LOCATION REPORT")
    txt_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    txt_lines.append(f"Sort Order: {'By ' + sort_by.title()}")
    txt_lines.append("="*50)
    txt_lines.append(f"{'Location':<30} {'Unique Patients':>15}")
    txt_lines.append("-"*50)
    
    # CSV data
    csv_rows = []
    csv_rows.append(['Location', 'Unique_Patients'])
    
    total_unique_patients = 0
    for location, count in sorted_items:
        # Console and txt format
        line = f"{location:<30} {count:>15}"
        report.append(line)
        txt_lines.append(line)
        
        # CSV format
        csv_rows.append([location, count])
        
        total_unique_patients += count
    
    # Add totals
    total_line = f"{'TOTAL':<30} {total_unique_patients:>15}"
    report.append("-"*50)
    report.append(total_line)
    report.append("="*50)
    
    txt_lines.append("-"*50)
    txt_lines.append(total_line)
    txt_lines.append("="*50)
    
    csv_rows.append(['TOTAL', total_unique_patients])
    
    # Write txt file
    try:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(txt_lines))
        print(f"\nLocation report written to: {txt_filename}")
    except Exception as e:
        print(f"Error writing txt file: {e}")
    
    # Write CSV file
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
        print(f"CSV report written to: {csv_filename}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")
    
    return "\n".join(report)

def analyze_data_gaps(data, output_prefix="data_gaps_analysis"):
    """
    Analyzes data quality by finding records with missing location or payor information.
    Args:
        data (list): A list of dictionaries containing client information
        output_prefix (str): Prefix for output filename
    Returns:
        dict: Summary of data gaps
    """
    has_payor_no_location = set()
    has_location_no_payor = set()
    has_both = 0
    has_neither = 0
    total_records = len(data)
    
    for row in data:
        location = row.get('Location', '').strip()
        payor = row.get('Payor', '').strip()
        patient = row.get('Patient', '').strip()
        
        if payor and not location:
            if patient:
                has_payor_no_location.add(patient)
        elif location and not payor:
            if patient:
                has_location_no_payor.add(patient)
        elif location and payor:
            has_both += 1
        else:
            has_neither += 1
    
    # Calculate percentages
    gaps_summary = {
        'total_records': total_records,
        'has_both': has_both,
        'has_both_pct': (has_both / total_records * 100) if total_records > 0 else 0,
        'payor_no_location': len(has_payor_no_location),
        'payor_no_location_pct': (len(has_payor_no_location) / total_records * 100) if total_records > 0 else 0,
        'location_no_payor': len(has_location_no_payor),
        'location_no_payor_pct': (len(has_location_no_payor) / total_records * 100) if total_records > 0 else 0,
        'has_neither': has_neither,
        'has_neither_pct': (has_neither / total_records * 100) if total_records > 0 else 0,
        'patients_payor_no_location': sorted(has_payor_no_location),
        'patients_location_no_payor': sorted(has_location_no_payor)
    }
    
    # Print summary to console
    print("\n" + "="*50)
    print("DATA QUALITY ANALYSIS - LOCATION REPORT")
    print("="*50)
    print(f"Total Records: {total_records}")
    print(f"Records with both Location and Payor: {has_both} ({gaps_summary['has_both_pct']:.1f}%)")
    print(f"Records with Payor but NO Location: {len(has_payor_no_location)} ({gaps_summary['payor_no_location_pct']:.1f}%)")
    print(f"Records with Location but NO Payor: {len(has_location_no_payor)} ({gaps_summary['location_no_payor_pct']:.1f}%)")
    print(f"Records with neither: {has_neither} ({gaps_summary['has_neither_pct']:.1f}%)")
    
    if len(has_payor_no_location) > 0:
        print(f"\nUnique patients with Payor but no Location: {len(has_payor_no_location)}")
        if len(has_payor_no_location) <= 10:
            for patient in sorted(has_payor_no_location)[:10]:
                print(f"  - {patient}")
    
    print("="*50)
    
    # Write detailed gaps analysis to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gaps_filename = f"{output_prefix}_location_{timestamp}.txt"
    
    try:
        with open(gaps_filename, 'w', encoding='utf-8') as f:
            f.write("DATA QUALITY ANALYSIS - LOCATION FOCUS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            f.write("SUMMARY\n")
            f.write("-"*50 + "\n")
            f.write(f"Total Records: {total_records}\n")
            f.write(f"Records with both Location and Payor: {has_both} ({gaps_summary['has_both_pct']:.1f}%)\n")
            f.write(f"Records with Payor but NO Location: {len(has_payor_no_location)} ({gaps_summary['payor_no_location_pct']:.1f}%)\n")
            f.write(f"Records with Location but NO Payor: {len(has_location_no_payor)} ({gaps_summary['location_no_payor_pct']:.1f}%)\n")
            f.write(f"Records with neither: {has_neither} ({gaps_summary['has_neither_pct']:.1f}%)\n\n")
            
            if len(has_payor_no_location) > 0:
                f.write("PATIENTS WITH PAYOR BUT NO LOCATION\n")
                f.write("-"*50 + "\n")
                for patient in sorted(has_payor_no_location):
                    f.write(f"{patient}\n")
        
        print(f"Data gaps analysis written to: {gaps_filename}")
    except Exception as e:
        print(f"Error writing gaps analysis file: {e}")
    
    return gaps_summary

def print_unique_client_list(data, target_location='ARDMORE'):
    """
    Extracts and prints a sorted list of unique client/patient names from a specific location.
    Args:
        data (list): A list of dictionaries containing client information
        target_location (str): The location to filter by (default: 'ARDMORE')
    """
    unique_patients = set()
    
    # Extract unique patient names from target location only
    for row in data:
        location = row.get('Location')
        patient = row.get('Patient')
        
        # Check if location matches target (case-insensitive comparison)
        if location and location.strip().upper() == target_location.upper() and patient and patient.strip():
            unique_patients.add(patient.strip())
    
    # Sort the names alphabetically
    sorted_patients = sorted(unique_patients)
    
    # Print the formatted list
    print("\n\n" + "="*50)
    print(f"UNIQUE CLIENTS/PATIENTS FROM {target_location.upper()}")
    print("="*50)
    
    if not sorted_patients:
        print(f"No patients found at {target_location} location.")
    else:
        for i, patient in enumerate(sorted_patients, 1):
            print(f"{i:4d}. {patient}")
    
    print("-"*50)
    print(f"Total unique clients at {target_location}: {len(sorted_patients)}")
    print("="*50)

def main():
    if len(sys.argv) < 2:
        print("Usage: python clientByLocation.py <csv_file_path>")
        sys.exit(1)
    
    dataPath = sys.argv[1]
    
    try:
        # Read the CSV data
        text = get_csv_data(dataPath)
        
        # Convert to dictionary format
        data = csv_to_dictionary(text)
        
        # Process the data to count unique patients by location
        location_count = process_client_by_location(data)
        
        # Generate output prefix from input filename
        import os
        base_name = os.path.splitext(os.path.basename(dataPath))[0]
        output_prefix = f"{base_name}_location_summary"
        
        # Generate and print the report (sorted alphabetically by location)
        print(generate_report(location_count, sort_by='location', output_prefix=output_prefix))
        
        # Optionally, also show sorted by count
        print("\n\nSame data sorted by unique patient count:")
        print(generate_report(location_count, sort_by='count', output_prefix=f"{output_prefix}_by_count"))
        
        # Analyze data quality gaps
        gaps_prefix = f"{base_name}_data_gaps"
        analyze_data_gaps(data, gaps_prefix)
        
        # Print the list of all unique clients
        print_unique_client_list(data)
        
    except FileNotFoundError:
        print(f"Error: File '{dataPath}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()