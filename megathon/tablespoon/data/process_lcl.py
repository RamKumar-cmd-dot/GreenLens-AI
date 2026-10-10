
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/external")
OUTPUT = Path("data/processed/lcl_household_features.csv")

files = sorted(DATA_DIR.glob("LCL-June2015v2_*.csv"))

if not files:
    raise FileNotFoundError("No matching LCL CSV files found")

print(f"Found {len(files)} CSV files")

# Aggregated consumption per household
totals = {}
counts = {}

for index, file in enumerate(files, start=1):
    print(f"Processing {index}/{len(files)}: {file.name}")

    for chunk in pd.read_csv(file, chunksize=100000):
        chunk.columns = chunk.columns.str.strip()

        required = [
            "LCLid",
            "KWH/hh (per half hour)"
        ]

        missing = set(required) - set(chunk.columns)
        if missing:
            raise ValueError(f"Missing columns in {file}: {missing}")

        chunk["kwh"] = pd.to_numeric(
            chunk["KWH/hh (per half hour)"],
            errors="coerce"
        )

        chunk = chunk.dropna(subset=["LCLid", "kwh"])
        chunk = chunk[chunk["kwh"] >= 0]

        grouped = chunk.groupby("LCLid")["kwh"].agg(
            ["sum", "count"]
        )

        for household, row in grouped.iterrows():
            totals[household] = (
                totals.get(household, 0)
                + row["sum"]
            )

            counts[household] = (
                counts.get(household, 0)
                + row["count"]
            )

results = []

for household, total in totals.items():
    count = counts[household]

    # Annualized estimate from average half-hour consumption.
    annual_kwh = (total / count) * 48 * 365

    results.append({
        "LCLid": household,
        "electricity_kwh_year": annual_kwh,
        "observed_kwh": total,
        "readings_count": count,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(results)
df.to_csv(OUTPUT, index=False)

print("\nProcessing completed!")
print("Households:", len(df))
print("Output:", OUTPUT)
print(df.head())
