import openpyxl

def fill_blank_cells(input_filename, output_filename):
    print(f"Loading '{input_filename}'...")
    
    # Load the Excel workbook
    try:
        workbook = openpyxl.load_workbook(input_filename)
    except FileNotFoundError:
        print("Error: The file was not found. Please check the file name and path.")
        return

    # Go through every sheet in the workbook
    for sheet in workbook.worksheets:
        # Check every cell in the current sheet
        for row in sheet.iter_rows():
            for cell in row:
                # If the cell is completely empty or just contains spaces
                if cell.value is None or str(cell.value).strip() == "":
                    cell.value = "n/a"

    # Save the changes to a new file (or overwrite the old one)
    workbook.save(output_filename)
    print(f"Success! The updated file has been saved as '{output_filename}'.")

fill_blank_cells('results/STEELITE_Updated_v0.0.3.xlsx', 'results/STEELITE_Updated_v0.0.4.xlsx')