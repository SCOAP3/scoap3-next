#!/bin/bash

#2
# Define the root directory to start the search from
root_dir="/data/harvesting/Elsevier/unpacked"  # Replace with your actual directory path
output_file="./outputfile.txt"

# Find all dataset.xml files and process each one with awk
find "$root_dir" -type f -name 'dataset.xml' | while IFS= read -r file; do

    # Get the last modification date of the file
    mod_date=$(ls -l --time-style=long-iso "$file" | awk '{print $6}')
    #mod_date="example"

    awk -v filepath="$file" -v mod_date="$mod_date" '
        BEGIN {
            # Extract the directory path from the full file path
            split(filepath, pathParts, "/");
            delete pathParts[length(pathParts)]; # Remove the last part (filename)
            dirPath = pathParts[1];
            for(i = 2; i <= length(pathParts); i++) {
                dirPath = dirPath "/" pathParts[i];
            }
        }
        /<doi>/ {
            gsub(/.*<doi>|<\/doi>.*/, "", $0);
            doi=$0;
            next;
        }
        doi != "" && /<pathname>.*\.xml<\/pathname>/ {
            gsub(/.*<pathname>|<\/pathname>.*/, "", $0);
            xml_path=dirPath "/" $0;
        }
        doi != "" && /<pathname>.*\.pdf<\/pathname>/ {
            gsub(/.*<pathname>|<\/pathname>.*/, "", $0);
            pdf_path=dirPath "/" $0;
            print doi, xml_path, pdf_path, mod_date;
            doi=""; xml_path=""; pdf_path="";
        }
    ' "$file" >> "$output_file"
done
echo "Processing complete. Results saved to $output_file"

