import pandas as pd

# Step 1: Load Dataset

movies = pd.read_csv("dataset/tmdb_5000_movies.csv")

credits = pd.read_csv("dataset/tmdb_5000_credits.csv")

print("Movies Dataset Loaded")
print("Credits Dataset Loaded")


# Step 2: Check Dataset Shape

print("\nMovies Shape:", movies.shape)

print("Credits Shape:", credits.shape)


# Step 3: Check Missing Values

print("\nMissing Values in Movies:")

print(movies.isnull().sum())


# Step 4: Check Duplicate Values

print("\nDuplicate Movies:")

print(movies.duplicated().sum())


# Step 5: Merge Both Datasets

movies = movies.merge(
    credits,
    left_on="id",
    right_on="movie_id"
)

print("\nDataset Merged Successfully")


# Step 6: Select Important Columns

movies = movies[
    [
        'movie_id',
        'title_x',
        'overview',
        'genres',
        'keywords',
        'cast',
        'crew'
    ]
]


# Step 7: Rename Movie Title

movies.rename(
    columns={'title_x': 'title'},
    inplace=True
)


# Step 8: Handle Missing Values

movies.dropna(inplace=True)


# Step 9: Remove Duplicate Movies

movies.drop_duplicates(inplace=True)


# Step 10: Display Clean Dataset

print("\nClean Dataset:")

print(movies.head())


# Step 11: Final Dataset Information

print("\nFinal Dataset Shape:")

print(movies.shape)


# Step 12: Save Clean Dataset

movies.to_csv(
    "dataset/cleaned_movies.csv",
    index=False
)

print("\nClean Dataset Saved Successfully!")