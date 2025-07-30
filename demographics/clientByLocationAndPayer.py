import sys
import csv
from io import StringIO

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

def process_client_by_location_and_payer(data):
    """
    Processes client data to group by location and then by payer, counting unique patients.
    Args:
        data (list): A list of dictionaries containing client information, where each dictionary
                     has 'Location', 'Payor', and 'Patient' keys.
    Returns:
        dict: A nested dictionary with locations as keys, containing dictionaries of payors
              with sets of unique patients.
    """
    location_payer_patients = {}  # Nested dict to track unique patients per location/payer
    
    for row in data:
        location = row.get('Location')
        payor = row.get('Payor')
        patient = row.get('Patient')
        
        # Skip rows without required fields
        if not all([location, payor, patient]) or not all([location.strip(), payor.strip(), patient.strip()]):
            continue
            
        location = location.strip()
        payor = payor.strip()
        patient = patient.strip()
        
        # Initialize nested structure if needed
        if location not in location_payer_patients:
            location_payer_patients[location] = {}
        
        if payor not in location_payer_patients[location]:
            location_payer_patients[location][payor] = set()
        
        # Add patient to the set (automatically handles duplicates)
        location_payer_patients[location][payor].add(patient)
    
    return location_payer_patients

def generate_hierarchical_report(location_payer_data, sort_by='location'):
    """
    Generates a formatted report of unique patient counts by location and payer.
    Args:
        location_payer_data (dict): Nested dictionary with locations and payors
        sort_by (str): 'location' for alphabetical or 'count' for by total count
    Returns:
        str: Formatted report string
    """
    if not location_payer_data:
        return "No client data found."
    
    # Calculate totals for each location
    location_totals = {}
    for location, payors in location_payer_data.items():
        total = sum(len(patients) for patients in payors.values())
        location_totals[location] = total
    
    # Sort locations
    if sort_by == 'count':
        sorted_locations = sorted(location_totals.items(), key=lambda x: (-x[1], x[0]))
    else:
        sorted_locations = sorted(location_totals.items())
    
    # Build the report
    report = []
    report.append("\n" + "="*70)
    report.append("UNIQUE PATIENT COUNT BY LOCATION AND PAYOR REPORT")
    report.append("="*70)
    
    grand_total = 0
    
    for location, location_total in sorted_locations:
        # Location header
        report.append(f"\n{location} (Total: {location_total} unique patients)")
        report.append("-" * 60)
        report.append(f"  {'Payor':<35} {'Unique Patients':>20}")
        report.append("  " + "-" * 55)
        
        # Sort payors within location by count
        payor_data = location_payer_data[location]
        sorted_payors = sorted(payor_data.items(), key=lambda x: (-len(x[1]), x[0]))
        
        for payor, patients in sorted_payors:
            count = len(patients)
            report.append(f"  {payor:<35} {count:>20}")
        
        grand_total += location_total
    
    # Grand total
    report.append("\n" + "="*70)
    report.append(f"{'GRAND TOTAL (All Locations)':<45} {grand_total:>20}")
    report.append("="*70)
    
    return "\n".join(report)

def generate_summary_report(location_payer_data, output_prefix="summary_report"):
    """
    Generates a summary matrix showing patient counts by location and payer.
    Writes the output to both txt and csv files.
    Args:
        location_payer_data (dict): Nested dictionary with locations and payors
        output_prefix (str): Prefix for output filenames
    Returns:
        str: Formatted summary matrix
    """
    import os
    from datetime import datetime
    
    # Collect all unique payors
    all_payors = set()
    for payors in location_payer_data.values():
        all_payors.update(payors.keys())
    
    sorted_payors = sorted(all_payors)
    sorted_locations = sorted(location_payer_data.keys())
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = f"{output_prefix}_{timestamp}.txt"
    csv_filename = f"{output_prefix}_{timestamp}.csv"
    
    # Build summary matrix for display and txt file
    report = []
    report.append("\n\n" + "="*70)
    report.append("SUMMARY MATRIX: Unique Patients by Location and Payor")
    report.append("="*70)
    
    # Create full matrix for txt file (not limited to 5 payors)
    txt_report = []
    txt_report.append("="*70)
    txt_report.append("SUMMARY MATRIX: Unique Patients by Location and Payor")
    txt_report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    txt_report.append("="*70)
    
    # Header for txt file
    txt_header = "Location" + "\t"
    for payor in sorted_payors:
        txt_header += payor + "\t"
    txt_header += "Total"
    txt_report.append(txt_header)
    txt_report.append("-" * 70)
    
    # Console display header (limited to 5 payors)
    header = f"{'Location':<20}"
    for payor in sorted_payors[:5]:
        header += f"{payor[:12]:>13}"
    if len(sorted_payors) > 5:
        header += "  ..."
    report.append(header)
    report.append("-" * 70)
    
    # Prepare CSV data
    csv_rows = []
    csv_header = ['Location'] + sorted_payors + ['Total']
    csv_rows.append(csv_header)
    
    # Data rows
    for location in sorted_locations:
        # Console display row (limited)
        row = f"{location:<20}"
        for payor in sorted_payors[:5]:
            count = len(location_payer_data[location].get(payor, set()))
            row += f"{count:>13}"
        if len(sorted_payors) > 5:
            row += "  ..."
        report.append(row)
        
        # Full data for txt and csv files
        txt_row = location + "\t"
        csv_row = [location]
        location_total = 0
        
        for payor in sorted_payors:
            count = len(location_payer_data[location].get(payor, set()))
            txt_row += str(count) + "\t"
            csv_row.append(count)
            location_total += count
        
        txt_row += str(location_total)
        csv_row.append(location_total)
        txt_report.append(txt_row)
        csv_rows.append(csv_row)
    
    # Add totals row
    txt_report.append("-" * 70)
    totals_row = "TOTAL\t"
    csv_totals = ['TOTAL']
    grand_total = 0
    
    for payor in sorted_payors:
        payor_total = sum(len(location_payer_data[loc].get(payor, set())) 
                         for loc in sorted_locations)
        totals_row += str(payor_total) + "\t"
        csv_totals.append(payor_total)
        grand_total += payor_total
    
    totals_row += str(grand_total)
    csv_totals.append(grand_total)
    txt_report.append(totals_row)
    csv_rows.append(csv_totals)
    
    # Write txt file
    try:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(txt_report))
        print(f"\nSummary report written to: {txt_filename}")
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
    
    # Track detailed information for combined report
    payor_only_by_payor = {}  # Dict of payors with their patients who have no location
    location_only_by_location = {}  # Dict of locations with their patients who have no payor
    
    for row in data:
        location = row.get('Location', '').strip()
        payor = row.get('Payor', '').strip()
        patient = row.get('Patient', '').strip()
        
        if payor and not location:
            if patient:
                has_payor_no_location.add(patient)
                if payor not in payor_only_by_payor:
                    payor_only_by_payor[payor] = set()
                payor_only_by_payor[payor].add(patient)
        elif location and not payor:
            if patient:
                has_location_no_payor.add(patient)
                if location not in location_only_by_location:
                    location_only_by_location[location] = set()
                location_only_by_location[location].add(patient)
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
    print("\n" + "="*70)
    print("DATA QUALITY ANALYSIS - COMPREHENSIVE REPORT")
    print("="*70)
    print(f"Total Records: {total_records}")
    print(f"Records with both Location and Payor: {has_both} ({gaps_summary['has_both_pct']:.1f}%)")
    print(f"Records with Payor but NO Location: {len(has_payor_no_location)} ({gaps_summary['payor_no_location_pct']:.1f}%)")
    print(f"Records with Location but NO Payor: {len(has_location_no_payor)} ({gaps_summary['location_no_payor_pct']:.1f}%)")
    print(f"Records with neither: {has_neither} ({gaps_summary['has_neither_pct']:.1f}%)")
    
    # Show summary by payor for missing locations
    if payor_only_by_payor:
        print("\nPayors with patients missing location data:")
        for payor, patients in sorted(payor_only_by_payor.items(), key=lambda x: -len(x[1]))[:5]:
            print(f"  {payor}: {len(patients)} patients")
    
    # Show summary by location for missing payors
    if location_only_by_location:
        print("\nLocations with patients missing payor data:")
        for location, patients in sorted(location_only_by_location.items(), key=lambda x: -len(x[1]))[:5]:
            print(f"  {location}: {len(patients)} patients")
    
    print("="*70)
    
    # Write detailed gaps analysis to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gaps_filename = f"{output_prefix}_combined_{timestamp}.txt"
    
    try:
        with open(gaps_filename, 'w', encoding='utf-8') as f:
            f.write("DATA QUALITY ANALYSIS - LOCATION AND PAYOR COMBINED\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            f.write("OVERALL SUMMARY\n")
            f.write("-"*50 + "\n")
            f.write(f"Total Records: {total_records}\n")
            f.write(f"Records with both Location and Payor: {has_both} ({gaps_summary['has_both_pct']:.1f}%)\n")
            f.write(f"Records with Payor but NO Location: {len(has_payor_no_location)} ({gaps_summary['payor_no_location_pct']:.1f}%)\n")
            f.write(f"Records with Location but NO Payor: {len(has_location_no_payor)} ({gaps_summary['location_no_payor_pct']:.1f}%)\n")
            f.write(f"Records with neither: {has_neither} ({gaps_summary['has_neither_pct']:.1f}%)\n\n")
            
            if payor_only_by_payor:
                f.write("BREAKDOWN: PAYORS WITH PATIENTS MISSING LOCATION\n")
                f.write("-"*50 + "\n")
                for payor, patients in sorted(payor_only_by_payor.items()):
                    f.write(f"\n{payor} ({len(patients)} patients):\n")
                    for patient in sorted(patients):
                        f.write(f"  - {patient}\n")
            
            if location_only_by_location:
                f.write("\n\nBREAKDOWN: LOCATIONS WITH PATIENTS MISSING PAYOR\n")
                f.write("-"*50 + "\n")
                for location, patients in sorted(location_only_by_location.items()):
                    f.write(f"\n{location} ({len(patients)} patients):\n")
                    for patient in sorted(patients):
                        f.write(f"  - {patient}\n")
        
        print(f"Data gaps analysis written to: {gaps_filename}")
    except Exception as e:
        print(f"Error writing gaps analysis file: {e}")
    
    return gaps_summary

def print_unique_client_list(data, target_location='ARDMORE', target_payor=None):
    """
    Extracts and prints a sorted list of unique client/patient names from a specific location and/or payor.
    Args:
        data (list): A list of dictionaries containing client information
        target_location (str): The location to filter by (default: 'ARDMORE')
        target_payor (str): The payor to filter by (optional)
    """
    unique_patients = set()
    
    # Extract unique patient names based on filters
    for row in data:
        location = row.get('Location')
        payor = row.get('Payor')
        patient = row.get('Patient')
        
        if not patient or not patient.strip():
            continue
            
        # Check location match
        location_match = location and location.strip().upper() == target_location.upper()
        
        # Check payor match (if specified)
        if target_payor:
            payor_match = payor and payor.strip().upper() == target_payor.upper()
            if location_match and payor_match:
                unique_patients.add(patient.strip())
        else:
            if location_match:
                unique_patients.add(patient.strip())
    
    # Sort the names alphabetically
    sorted_patients = sorted(unique_patients)
    
    # Print the formatted list
    print("\n\n" + "="*50)
    if target_payor:
        print(f"UNIQUE CLIENTS FROM {target_location.upper()} - {target_payor.upper()}")
    else:
        print(f"UNIQUE CLIENTS FROM {target_location.upper()} - ALL PAYORS")
    print("="*50)
    
    if not sorted_patients:
        print("No patients found with specified criteria.")
    else:
        for i, patient in enumerate(sorted_patients, 1):
            print(f"{i:4d}. {patient}")
    
    print("-"*50)
    print(f"Total unique clients: {len(sorted_patients)}")
    print("="*50)

def main():
    if len(sys.argv) < 2:
        print("Usage: python clientByLocationAndPayer.py <csv_file_path>")
        sys.exit(1)
    
    dataPath = sys.argv[1]
    
    try:
        # Read the CSV data
        text = get_csv_data(dataPath)
        
        # Convert to dictionary format
        data = csv_to_dictionary(text)
        
        # Process the data to count unique patients by location and payer
        location_payer_data = process_client_by_location_and_payer(data)
        
        # Generate and print the hierarchical report
        print(generate_hierarchical_report(location_payer_data, sort_by='location'))
        
        # Generate output prefix from input filename
        import os
        base_name = os.path.splitext(os.path.basename(dataPath))[0]
        output_prefix = f"{base_name}_summary"
        
        # Generate and print the summary matrix (also writes to files)
        print(generate_summary_report(location_payer_data, output_prefix))
        
        # Analyze data quality gaps
        gaps_prefix = f"{base_name}_data_gaps"
        analyze_data_gaps(data, gaps_prefix)
        
        # Print unique clients from ARDMORE for all payors
        print_unique_client_list(data, 'ARDMORE')
        
        # Example: Print unique clients from ARDMORE with Medicare
        # print_unique_client_list(data, 'ARDMORE', 'Medicare')
        
    except FileNotFoundError:
        print(f"Error: File '{dataPath}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()