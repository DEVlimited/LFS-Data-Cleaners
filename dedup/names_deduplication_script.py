def process_names(names_text):
    """
    Process a list of names to remove duplicates and count unique names.
    
    Args:
        names_text (str): Multi-line string containing names in "Last, First" format
    
    Returns:
        tuple: (unique_names_set, total_unique_count)
    """
    # Split the text into individual lines
    lines = names_text.strip().split('\n')
    
    # Remove empty lines and strip whitespace
    names = [line.strip() for line in lines if line.strip()]
    
    # Create a set to store unique names
    unique_names = set(names)
    
    # Count total unique names
    total_unique = len(unique_names)
    
    return unique_names, total_unique

def analyze_names(names_text):
    """
    Analyze the names list and provide detailed statistics.
    """
    # Get unique names
    unique_names, total_unique = process_names(names_text)
    
    # Sort names alphabetically
    sorted_names = sorted(unique_names)
    
    # Count names with special notations
    names_with_notation = [name for name in unique_names if any(notation in name for notation in ['INS/MED', 'MED/INS', 'BCBS/MED'])]
    
    # Print results
    print(f"Total number of unique names: {total_unique}")
    print(f"Number of names with medical/insurance notations: {len(names_with_notation)}")
    print(f"\nFirst 10 unique names (alphabetically):")
    for i, name in enumerate(sorted_names[:10], 1):
        print(f"{i}. {name}")
    
    print(f"\nLast 10 unique names (alphabetically):")
    for i, name in enumerate(sorted_names[-10:], len(sorted_names)-9):
        print(f"{i}. {name}")
    
    return sorted_names

# If you want to use this script with the names from your file:
if __name__ == "__main__":
    # You can paste your names here or read from a file
    names_text = """Reed, Bobby
    Example, Example"""
    
    # For full list, save to file and read:
    # with open('names.txt', 'r') as f:
    #     names_text = f.read()
    
    # Analyze the names
    sorted_names = analyze_names(names_text)
    
    # Optional: Save unique names to a file
    with open('unique_names.txt', 'w') as f:
        for name in sorted_names:
            f.write(name + '\n')
    print(f"\nUnique names have been saved to 'unique_names.txt'")
