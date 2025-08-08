import pandas as pd
import re

input_file = "fully-enriched-dataset.csv"
output_file = "final_results.csv"

def parse_max_floors(bauzonen):
    # Extract max floors from bauzonen string
    match = re.search(r"(\d+) und mehr Vollgeschosse", bauzonen)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+) Vollgeschosse", bauzonen)
    if match:
        return int(match.group(1))
    return None

def score_entry(row):
    score = 0
    comment_parts = []
    # Parse floors
    try:
        current_floors = int(row.get("Number of floors", 0))
    except:
        current_floors = 0
    max_floors = parse_max_floors(str(row.get("bauzonen", "")))
    if max_floors and current_floors < max_floors:
        diff = max_floors - current_floors
        score += 60 + diff * 15
        comment_parts.append(f"Can add {diff} floors")
    # Year of construction
    try:
        year = int(row.get("Year of construction of the building", 0))
        if year > 0:
            if year < 1950:
                score += 40 + (1950 - year) * 0.3
                comment_parts.append(f"Very old building ({year})")
            elif year < 1985:
                score += 30 + (1985 - year) * 0.2
                comment_parts.append(f"Old building ({year})")
    except:
        pass
    # Building area
    try:
        area = float(row.get("Building area [m2]", 0))
        if 500 <= area <= 1000:
            score += 50
            comment_parts.append(f"Ideal size ({int(area)} m2)")
        elif 300 <= area < 500 or 1000 < area <= 1500:
            score += 30
            comment_parts.append(f"Good size ({int(area)} m2)")
        else:
            score += min(area / 20, 10)
    except:
        pass
    # Number of apartments
    try:
        apartments = int(row.get("Number of apartments", 0))
        if apartments >= 8:
            score += 20
            comment_parts.append(f"Many apartments ({apartments})")
        elif apartments >= 4:
            score += 10
            comment_parts.append(f"Several apartments ({apartments})")
        elif apartments > 0:
            score += 5
            comment_parts.append(f"Few apartments ({apartments})")
    except:
        pass
    # Location bonus (Zurich city ZIPs: 8000-8099)
    try:
        zip_label = str(row.get("ZIP_LABEL", ""))
        zip_num = int(re.findall(r"\d+", zip_label)[0]) if re.findall(r"\d+", zip_label) else None
        if zip_num and 8000 <= zip_num <= 8099:
            score += 15
            comment_parts.append("Prime Zurich location")
    except:
        pass
    # Low occupancy bonus
    try:
        apartments = int(row.get("Number of apartments", 0))
        if apartments <= 2:
            score += 5
            comment_parts.append("Easy to redevelop")
    except:
        pass
    # Final comment
    if score > 120:
        comment_parts.append("Outstanding redevelopment potential")
    elif score > 80:
        comment_parts.append("Excellent investment potential")
    elif score > 50:
        comment_parts.append("Good investment potential")
    else:
        comment_parts.append("Some potential for improvement")
    comment = ", ".join(comment_parts)
    return score, comment

def make_address(row):
    street = str(row.get("STN_LABEL", "")).strip()
    number = str(row.get("ADR_NUMBER", "")).strip()
    zip_label = str(row.get("ZIP_LABEL", "")).strip()
    parts = []
    if street:
        parts.append(street)
    if number:
        parts.append(number)
    address_main = " ".join(parts) if parts else "Unknown address"
    address_full = f"{address_main}, {zip_label}" if zip_label else address_main
    return address_full

# Read data
df = pd.read_csv(input_file, sep=";")
results = []
for _, row in df.iterrows():
    score, comment = score_entry(row)
    address = make_address(row)
    # Normalize score to 1-10
    norm_score = max(1, min(10, round((score / 150) * 9 + 1, 2)))
    try:
        area = float(row.get("Building area [m2]", 0))
    except:
        area = 0
    if 500 <= area <= 1000 and norm_score >= 6:
        results.append({
            "Investment score": norm_score,
            "Address": address,
            "Bauzonen": row.get("bauzonen", ""),
            "Year of construction of the building": row.get("Year of construction of the building", ""),
            "Building area [m2]": row.get("Building area [m2]", ""),
            "Number of floors": row.get("Number of floors", ""),
            "Number of apartments": row.get("Number of apartments", ""),
            "Comment": comment
        })
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by="Investment score", ascending=False)
results_df.to_csv(output_file, sep=";", index=False)
print(f"Results written to {output_file}")

# Export top 50 entries to a second CSV
top_50 = results_df.head(50)
top_50.to_csv("50-best investment-options.csv", sep=";", index=False)
print("Top 50 investment options written to 50-best investment-options.csv")
