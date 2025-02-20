import csv
import os
from dotenv import load_dotenv

load_dotenv()

csv_ins_str = os.getenv("CSV_INS")  # Get the combined CSV input string
csv_out = os.getenv("CSV_OUT")
try:
    with open(csv_out, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)

        # outfile.seek(0, os.SEEK_END)
        # is_empty = outfile.tell() == 0
        # if is_empty:
        writer.writerow(["name", "chapter"] + next(csv.reader(open(csv_ins_str.split(',')[0].split('|')[1], 'r')))) # write header only once

        for item in csv_ins_str.split(','):  # Split into individual file/chapter pairs
            try:
                upanishad_name, csv_in, chapter = item.split('|')
                with open(csv_in, 'r', newline='', encoding='utf-8') as infile:
                    reader = csv.reader(infile)
                    next(reader) # skip header from input file
                    for row in reader:
                        new_row = [upanishad_name, chapter] + row
                        writer.writerow(new_row)
            except FileNotFoundError:
                print(f"Error: Input file '{csv_in}' not found.")
            except ValueError:
                print(f"Error: Invalid CSV_INS format for item: '{item}'.  Expected upanishad_name|filepath|chapter.")
            except Exception as e:
                print(f"An error occurred while processing '{csv_in}': {e}")


except Exception as e:
    print(f"An error occurred: {e}")

print(f"Finished processing CSV files. Output written to '{csv_out}'.")