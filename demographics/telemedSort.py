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

def process_telemedicine_data(data):
    """
    Processes data to count telemedicine services and track patients who used them.
    Args:
        data (list): A list of dictionaries containing service information
    Returns:
        tuple: (total_count, patient_details_dict, location_summary_dict, payor_summary_dict)
    """
    total_count = 0
    patient_details = {}  # Dict to track each patient's telemedicine count
    location_summary = {}  # Dict to track telemedicine by location
    payor_summary = {}  # Dict to track telemedicine by payor
    
    for row in data:
        service = row.get('Service', '')
        patient = row.get('Patient', '')
        location = row.get('Location', '')
        payor = row.get('Payor', '')
        
        # Check if service contains "Telemedicine" (case-insensitive)
        if 'telemedicine' in service.lower():
            total_count += 1
            
            # Track patient details
            if patient and patient.strip():
                patient = patient.strip()
                if patient not in patient_details:
                    patient_details[patient] = {
                        'count': 0,
                        'locations': set(),
                        'payors': set()
                    }
                patient_details[patient]['count'] += 1
                
                if location and location.strip():
                    patient_details[patient]['locations'].add(location.strip())
                if payor and payor.strip():
                    patient_details[patient]['payors'].add(payor.strip())
            
            # Track location summary
            if location and location.strip():
                location = location.strip()
                location_summary[location] = location_summary.get(location, 0) + 1
            
            # Track payor summary
            if payor and payor.strip():
                payor = payor.strip()
                payor_summary[payor] = payor_summary.get(payor, 0) + 1
    
    return total_count, patient_details, location_summary, payor_summary

def generate_telemedicine_report(total_count, patient_details, location_summary, payor_summary, output_prefix="telemedicine_report"):
    """
    Generates a comprehensive telemedicine report and writes to files.
    """
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = f"{output_prefix}_{timestamp}.txt"
    csv_filename = f"{output_prefix}_{timestamp}.csv"
    
    # Build the report
    report_lines = []
    report_lines.append("="*70)
    report_lines.append("TELEMEDICINE SERVICE REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("="*70)
    report_lines.append(f"\nTOTAL TELEMEDICINE SERVICES: {total_count}")
    report_lines.append(f"UNIQUE PATIENTS USING TELEMEDICINE: {len(patient_details)}")
    
    # Location Summary
    report_lines.append("\n" + "-"*50)
    report_lines.append("TELEMEDICINE BY LOCATION")
    report_lines.append("-"*50)
    report_lines.append(f"{'Location':<30} {'Count':>15}")
    report_lines.append("-"*50)
    
    for location, count in sorted(location_summary.items(), key=lambda x: (-x[1], x[0])):
        report_lines.append(f"{location:<30} {count:>15}")
    
    # Payor Summary
    report_lines.append("\n" + "-"*50)
    report_lines.append("TELEMEDICINE BY PAYOR")
    report_lines.append("-"*50)
    report_lines.append(f"{'Payor':<30} {'Count':>15}")
    report_lines.append("-"*50)
    
    for payor, count in sorted(payor_summary.items(), key=lambda x: (-x[1], x[0])):
        report_lines.append(f"{payor:<30} {count:>15}")
    
    # Patient Details
    report_lines.append("\n" + "-"*50)
    report_lines.append("PATIENT TELEMEDICINE USAGE DETAILS")
    report_lines.append("-"*50)
    report_lines.append(f"{'Patient':<25} {'Count':>8} {'Location(s)':<20} {'Payor(s)':<20}")
    report_lines.append("-"*70)
    
    # Sort patients by count (descending), then by name
    sorted_patients = sorted(patient_details.items(), key=lambda x: (-x[1]['count'], x[0]))
    
    csv_rows = []
    csv_rows.append(['Patient', 'Telemedicine_Count', 'Locations', 'Payors'])
    
    for patient, details in sorted_patients:
        locations_str = ', '.join(sorted(details['locations']))
        payors_str = ', '.join(sorted(details['payors']))
        
        # Format for display (truncate if too long)
        loc_display = locations_str[:18] + '..' if len(locations_str) > 20 else locations_str
        pay_display = payors_str[:18] + '..' if len(payors_str) > 20 else payors_str
        
        report_lines.append(f"{patient:<25} {details['count']:>8} {loc_display:<20} {pay_display:<20}")
        
        # Full data for CSV
        csv_rows.append([patient, details['count'], locations_str, payors_str])
    
    report_lines.append("-"*70)
    report_lines.append("="*70)
    
    # Write txt file
    try:
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        print(f"\nTelemedicine report written to: {txt_filename}")
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
    
    # Return console display version
    return "\n".join(report_lines[:50])  # Limit console output

def print_telemedicine_summary(total_count, patient_details):
    """
    Prints a summary of telemedicine usage to console.
    """
    print("\n" + "="*50)
    print("TELEMEDICINE SERVICE SUMMARY")
    print("="*50)
    print(f"Total Telemedicine Services: {total_count}")
    print(f"Unique Patients: {len(patient_details)}")
    
    if patient_details:
        avg_per_patient = total_count / len(patient_details)
        print(f"Average Services per Patient: {avg_per_patient:.1f}")
        
        # Find top users
        top_users = sorted(patient_details.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        print("\nTop 5 Telemedicine Users:")
        print("-"*50)
        for patient, details in top_users:
            print(f"  {patient}: {details['count']} services")
    
    print("="*50)

def main():
    if len(sys.argv) < 2:
        print("Usage: python telemedSort.py <csv_file_path>")
        sys.exit(1)
    
    dataPath = sys.argv[1]
    
    try:
        # Read the CSV data
        text = get_csv_data(dataPath)
        
        # Convert to dictionary format
        data = csv_to_dictionary(text)
        
        # Process the telemedicine data
        total_count, patient_details, location_summary, payor_summary = process_telemedicine_data(data)
        
        # Generate output prefix from input filename
        import os
        base_name = os.path.splitext(os.path.basename(dataPath))[0]
        output_prefix = f"{base_name}_telemedicine"
        
        # Generate and save the detailed report
        report = generate_telemedicine_report(
            total_count, 
            patient_details, 
            location_summary, 
            payor_summary,
            output_prefix
        )
        
        # Print summary to console
        print_telemedicine_summary(total_count, patient_details)
        
        # Print a portion of the detailed report
        print("\n(Full detailed report saved to files)")
        print(report)
        
    except FileNotFoundError:
        print(f"Error: File '{dataPath}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()