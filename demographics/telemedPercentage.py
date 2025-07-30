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

def process_okc_telemedicine_percentage(data):
    """
    Processes data to calculate telemedicine percentage for each patient at OKC location.
    Args:
        data (list): A list of dictionaries containing service information
    Returns:
        dict: Dictionary with patient as key and {total_visits, telemed_visits, percentage} as value
    """
    patient_stats = {}
    
    for row in data:
        location = row.get('Location', '').strip()
        patient = row.get('Patient', '').strip()
        service = row.get('Service', '').strip()
        
        # Only process OKC location records
        if location.upper() == 'OKC' and patient:
            if patient not in patient_stats:
                patient_stats[patient] = {
                    'total_visits': 0,
                    'telemed_visits': 0,
                    'percentage': 0.0,
                    'payors': set(),
                    'services': set()
                }
            
            # Count total visit
            patient_stats[patient]['total_visits'] += 1
            
            # Count telemedicine visit
            if 'telemedicine' in service.lower():
                patient_stats[patient]['telemed_visits'] += 1
            
            # Track payors and services for additional info
            payor = row.get('Payor', '').strip()
            if payor:
                patient_stats[patient]['payors'].add(payor)
            if service:
                patient_stats[patient]['services'].add(service)
    
    # Calculate percentages
    for patient, stats in patient_stats.items():
        if stats['total_visits'] > 0:
            stats['percentage'] = (stats['telemed_visits'] / stats['total_visits']) * 100
    
    return patient_stats

def generate_telemedicine_percentage_report(patient_stats, output_prefix="okc_telemed_percentage"):
    """
    Generates report showing telemedicine usage percentage for OKC patients.
    """
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = f"{output_prefix}_{timestamp}.txt"
    csv_filename = f"{output_prefix}_{timestamp}.csv"
    
    # Sort patients by percentage (descending), then by name
    sorted_patients = sorted(patient_stats.items(), 
                           key=lambda x: (-x[1]['percentage'], -x[1]['telemed_visits'], x[0]))
    
    # Build text report
    report_lines = []
    report_lines.append("="*80)
    report_lines.append("TELEMEDICINE USAGE PERCENTAGE REPORT - OKC LOCATION")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("="*80)
    report_lines.append(f"\nTotal OKC Patients: {len(patient_stats)}")
    
    # Calculate summary statistics
    total_visits_all = sum(stats['total_visits'] for stats in patient_stats.values())
    total_telemed_all = sum(stats['telemed_visits'] for stats in patient_stats.values())
    overall_percentage = (total_telemed_all / total_visits_all * 100) if total_visits_all > 0 else 0
    
    report_lines.append(f"Total OKC Visits: {total_visits_all}")
    report_lines.append(f"Total Telemedicine Visits: {total_telemed_all}")
    report_lines.append(f"Overall Telemedicine Usage: {overall_percentage:.1f}%")
    
    # Count usage tiers
    high_users = sum(1 for stats in patient_stats.values() if stats['percentage'] >= 75)
    medium_users = sum(1 for stats in patient_stats.values() if 25 <= stats['percentage'] < 75)
    low_users = sum(1 for stats in patient_stats.values() if 0 < stats['percentage'] < 25)
    no_telemed = sum(1 for stats in patient_stats.values() if stats['percentage'] == 0)
    
    report_lines.append(f"\nUsage Distribution:")
    report_lines.append(f"  High (≥75%): {high_users} patients")
    report_lines.append(f"  Medium (25-74%): {medium_users} patients")
    report_lines.append(f"  Low (1-24%): {low_users} patients")
    report_lines.append(f"  None (0%): {no_telemed} patients")
    
    # Detailed patient table
    report_lines.append("\n" + "-"*80)
    report_lines.append("PATIENT DETAILS")
    report_lines.append("-"*80)
    report_lines.append(f"{'Patient':<30} {'Total':>8} {'Telemed':>8} {'Percentage':>12} {'Payors':<20}")
    report_lines.append("-"*80)
    
    # Prepare CSV data
    csv_rows = []
    csv_rows.append(['Patient', 'Total_Visits', 'Telemed_Visits', 'Percentage', 'Payors'])
    
    # Console display
    console_lines = report_lines.copy()
    
    for patient, stats in sorted_patients:
        payors_str = ', '.join(sorted(stats['payors']))
        
        # Format percentage with color indicator
        pct = stats['percentage']
        pct_str = f"{pct:>11.1f}%"
        
        # Full line for file
        line = f"{patient:<30} {stats['total_visits']:>8} {stats['telemed_visits']:>8} {pct_str} {payors_str[:18] + '..' if len(payors_str) > 20 else payors_str:<20}"
        report_lines.append(line)
        
        # CSV row
        csv_rows.append([patient, stats['total_visits'], stats['telemed_visits'], f"{pct:.1f}", payors_str])
    
    report_lines.append("-"*80)
    report_lines.append("="*80)
    
    # Write txt file
    try:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        print(f"\nTelemedicine percentage report written to: {txt_filename}")
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
    
    # Return console display (limited to first 40 lines + summary)
    if len(console_lines) > 40:
        return "\n".join(console_lines[:40] + ["\n... (see full report in file)"] + report_lines[-3:])
    return "\n".join(console_lines + report_lines[-3:])

def print_telemedicine_insights(patient_stats):
    """
    Prints additional insights about telemedicine usage patterns.
    """
    if not patient_stats:
        print("\nNo OKC patients found in the data.")
        return
    
    print("\n" + "="*50)
    print("TELEMEDICINE USAGE INSIGHTS - OKC")
    print("="*50)
    
    # Find exclusive telemedicine users
    exclusive_telemed = [p for p, s in patient_stats.items() if s['percentage'] == 100 and s['total_visits'] > 0]
    if exclusive_telemed:
        print(f"\nPatients using ONLY telemedicine: {len(exclusive_telemed)}")
        for patient in sorted(exclusive_telemed)[:5]:
            visits = patient_stats[patient]['total_visits']
            print(f"  - {patient}: {visits} visit{'s' if visits > 1 else ''}")
    
    # Find high-volume telemedicine users
    high_volume = [(p, s) for p, s in patient_stats.items() if s['telemed_visits'] >= 5]
    if high_volume:
        high_volume.sort(key=lambda x: -x[1]['telemed_visits'])
        print(f"\nHigh-volume telemedicine users (≥5 telemed visits):")
        for patient, stats in high_volume[:5]:
            print(f"  - {patient}: {stats['telemed_visits']} telemed visits ({stats['percentage']:.1f}%)")
    
    print("="*50)

def main():
    if len(sys.argv) < 2:
        print("Usage: python telemedPercentage.py <csv_file_path>")
        sys.exit(1)
    
    dataPath = sys.argv[1]
    
    try:
        # Read the CSV data
        text = get_csv_data(dataPath)
        
        # Convert to dictionary format
        data = csv_to_dictionary(text)
        
        # Process OKC telemedicine data
        patient_stats = process_okc_telemedicine_percentage(data)
        
        if not patient_stats:
            print("\nNo patients found at OKC location.")
            print("Please check that 'OKC' exists in your Location column.")
            sys.exit(0)
        
        # Generate output prefix from input filename
        import os
        base_name = os.path.splitext(os.path.basename(dataPath))[0]
        output_prefix = f"{base_name}_okc_telemed_percentage"
        
        # Generate and display the report
        report = generate_telemedicine_percentage_report(patient_stats, output_prefix)
        print(report)
        
        # Print additional insights
        print_telemedicine_insights(patient_stats)
        
    except FileNotFoundError:
        print(f"Error: File '{dataPath}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()