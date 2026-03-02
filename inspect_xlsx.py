import openpyxl
import pandas as pd

# Read using pandas to see the structure
df = pd.read_excel('sources/STEELITE.xlsx')
print("Column names:")
print(df.columns.tolist())
print("\nDataframe shape:", df.shape)
print("\nFirst 3 rows:")
print(df.head(3))
print("\nData types:")
print(df.dtypes)
