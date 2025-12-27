import os
import argparse
from agent.file_io import read_txt, read_docx, write_txt, write_docx
from agent.planner import create_itinerary

def parse_input_content(content: str) -> dict:
    """
    Parses natural language or structured text into a preferences dict.
    Simple keyword parsing for now.
    """
    preferences = {}
    lines = content.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key == 'destination':
                preferences['destination'] = value
            elif key == 'duration':
                try:
                    preferences['duration'] = int(value.split()[0]) # handle "3 days"
                except:
                    preferences['duration'] = 3
            elif key == 'interests':
                preferences['interests'] = [i.strip() for i in value.split(',')]
            elif key == 'start date':
                preferences['start_date'] = value
    
    return preferences

def main():
    parser = argparse.ArgumentParser(description="Trip Itinerary Planner Agent")
    parser.add_argument("--input", "-i", type=str, help="Path to input file (.txt or .docx)", required=False)
    parser.add_argument("--output", "-o", type=str, help="Path to output file (.txt or .docx)", required=False)
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    
    # Interactive mode if arguments not provided
    if not input_path:
        print("Welcome to Trip Itinerary Planner!")
        input_path = input("Enter path to input file (e.g., input.txt): ")
        if not output_path:
            output_path = input("Enter path to output file (e.g., plan.docx): ")
            
    # Read input
    print(f"Reading from {input_path}...")
    ext = os.path.splitext(input_path)[1].lower()
    try:
        if ext == '.docx':
            content = read_docx(input_path)
        else:
            content = read_txt(input_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Process
    print("Generating itinerary...")
    preferences = parse_input_content(content)
    if not preferences:
        print("Could not parse preferences. Ensure format is 'Key: Value'")
        return
        
    itinerary = create_itinerary(preferences)
    
    # Write output
    print(f"Writing to {output_path}...")
    out_ext = os.path.splitext(output_path)[1].lower()
    try:
        if out_ext == '.docx':
            write_docx(output_path, itinerary)
        else:
            write_txt(output_path, itinerary)
        print("Done! Safe travels.")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    main()
