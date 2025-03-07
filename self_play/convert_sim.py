import os
import re
import argparse

def parse_file(input_file, output_folder):
    output_file = os.path.join(output_folder, os.path.basename(input_file).replace('.txt', '_converted.txt'))
    with open(input_file, 'r') as f_in:
        with open(output_file, 'w') as f_out:
            for line in f_in:
                parsed_line = re.sub(r'\{[^}]*\}', '', line)  # Remove text within curly braces
                parsed_line = parsed_line.replace('🧑‍💻', 'user').replace('🤖', 'assistant')
                f_out.write(parsed_line)

def main():
    parser = argparse.ArgumentParser(description='Parse and convert text files.')
    parser.add_argument('--input', help='Input folder path containing text files')
    args = parser.parse_args()

    output_folder = args.input + "_converted"
    os.makedirs(output_folder, exist_ok=True)

    input_folder = args.input
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.txt'):
            input_file_path = os.path.join(input_folder, file_name)
            parse_file(input_file_path, output_folder)

if __name__ == "__main__":
    main()
