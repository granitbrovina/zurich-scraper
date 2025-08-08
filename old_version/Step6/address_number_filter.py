import pandas as pd
import re

def is_number_only(address_number):
    """Return True if address_number contains only digits."""
    return bool(re.fullmatch(r"\d+", str(address_number)))

input_file = "enriched-zh-part2.csv"
output_file = "address-number-test.csv"

df = pd.read_csv(input_file, sep=";")

# Filter rows where ADR_NUMBER is only digits
filtered_df = df[df["ADR_NUMBER"].apply(is_number_only)]

filtered_df.to_csv(output_file, sep=";", index=False)
print(f"Filtered addresses written to {output_file}")
