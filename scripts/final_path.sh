#!/bin/bash
# scoap3-worker-69f8c4c579-6lrv9
#3
# Define file paths
output_file="./outputfile.txt"  # Path to the output file
additional_data_file="./missing_files.txt"  # Path to the additional data file
result_file="./final_missing_paths.txt"  # Path to the result file

# Clear the result file if it already exists
> "$result_file"

# Read each line of the additional data file
while IFS= read -r line; do
    # Extract the DOI and file type
    IFS=', ' read -r -a fields <<< "$line"
    doi=${fields[2]}
    file_type=${fields[1]}

    # Search for the DOI in the output file and append the line with file_type to the result file
    grep "$doi" "$output_file" | while read -r output_line; do
        echo "$output_line File Type: $file_type" >> "$result_file"
    done
done < "$additional_data_file"

echo "Processing complete. Results saved to $result_file"
