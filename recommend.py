import pandas as pd

# Load original dataset
original = pd.read_csv("dataset/tmdb_5000_movies.csv")

# Remove extra spaces and BOM from column names
original.columns = (
    original.columns
    .str.strip()
    .str.replace('\ufeff', '', regex=False)
)

print("\n========== CSV COLUMN NAMES ==========")

for column in original.columns:
    print(column)

print("\n========== POSTER CHECK ==========")

if "poster_path" in original.columns:
    print("SUCCESS: poster_path column mil gaya!")
    print(original[["title", "poster_path"]].head(10))

else:
    print("ERROR: poster_path column nahi mila!")
    print("Available columns:", original.columns.tolist())

print("\n========== DATASET CHECK COMPLETE ==========")