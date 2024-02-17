import ast
import csv
from itertools import combinations
import itertools
import time
from gensim.models import Word2Vec
import pandas as pd


def calculate_similarity(word1, word2):
    # Tokenize the input words
    tokens_word1 = word1.split()
    tokens_word2 = word2.split()

    # Compute similarity between all token pairs
    similarity_scores = []
    for token1 in tokens_word1:
        for token2 in tokens_word2:
            if token1 in model.wv.key_to_index and token2 in model.wv.key_to_index:
                score = model.wv.similarity(token1, token2)
                similarity_scores.append(score)
            else:
                continue

    return (sum(similarity_scores) / len(similarity_scores)) if (similarity_scores) else 0.0


def has_shared_words(ingredient1, ingredient2):
    '''
    Check if two ingredients have any shared words
    '''
    return not set(ingredient1.split()).isdisjoint(ingredient2.split())


# Load your Word2Vec model
model = Word2Vec.load("ingredient_word2vec.model")
print("Model loaded successfully")

# Generate a set of all unique ingredients
all_ingredients = set()

total_rows = 2240000
rows = 0
chunksize = 5000

############### ~ 1 minute to generate set ###############
start = time.time()
pairs_df = pd.DataFrame([], columns=[
    'Ingredient1', 'Ingredient2'])

for chunk in pd.read_csv('dataset/full_dataset.csv',
                         chunksize=chunksize):  # Adjust chunksize as needed
    print(f"Processing rows {rows} of {total_rows}")
    rows += chunksize

    # Update the set of all ingredients
    chunk['NER'] = chunk['NER'].apply(ast.literal_eval)

    # Flatten the lists of ingredients in the current chunk
    ingredients_iterable = itertools.chain.from_iterable(chunk['NER'])
    banned_symbols = [
        '\'', '+', '*', '(', ')', '&', '%', '/', '#', '\"', '!', '?',
        '.', ',']
    ingredients_iterable = [
        ingredient for ingredient in ingredients_iterable
        if not any(symbol in ingredient for symbol in banned_symbols)]

    # Update the set of all ingredients with the ingredients from the current chunk
    all_ingredients.update(ingredients_iterable)

print(
    f"All ingredients set loaded successfully in {time.time() - start} seconds")

# Convert the set of all ingredients into a list, sorted so similar ingredients are grouped together
all_ingredients = sorted(list(all_ingredients))
ingredient_pairs = []

############### ~ 5 minutes to generate pairs ###############
# Generate unique pairs from segments of the ingredients set of size chunk
for i in range(0, len(all_ingredients), chunksize):
    ingredients = all_ingredients[i: i + chunksize]
    num_processed = i + len(ingredients)

    # Generate all unique pairs of ingredients that have shared words
    start = time.time()
    pairs_chunk = [(a, b) for a, b in combinations(
        ingredients, 2) if has_shared_words(a, b)]
    print(
        f"Succesfully generated pairs for {num_processed} out of {len(all_ingredients)} ingredients in {time.time() - start} seconds")

    # Extend the list of ingredient pairs
    ingredient_pairs.extend(pairs_chunk)

# Apply the calculate_similarity function to each row
############### ~ 20 minutes to compute similarities ###############
chunksize *= 50
m = len(ingredient_pairs)

# Open a CSV file to write the similarities along with the pair names
hash = str(int(time.time()))
net_start = time.time()
with open(f"similarities_{hash}.csv", "w", newline="") as csvfile:
    # Define CSV writer
    fieldnames = ["Ingredient1", "Ingredient2", "Similarity"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Calculate similarity for each pair
    for i in range(0, m, chunksize):
        start_time = time.time()
        chunk_end = min(i + chunksize, m)
        chunk = ingredient_pairs[i:chunk_end]

        # Calculate and write similarity for each pair to the CSV file
        for pair in chunk:
            similarity = calculate_similarity(pair[0], pair[1])
            writer.writerow(
                {"Ingredient1": pair[0],
                 "Ingredient2": pair[1],
                 "Similarity": similarity})

        print(
            f"Similarities for {chunk_end} out of {m} computed successfully in {time.time() - start_time} seconds")

print(
    f"All similarities computed and written to CSV file in {time.time() - net_start} seconds.")

# Save the similarity scores
# Get a DF from the CSV file
similarity_scores_df = pd.read_csv(f"similarities_{hash}.csv")

# Filter out pairs with low similarity
filtered_pairs_df = similarity_scores_df[similarity_scores_df['Similarity'] > 0.85]
print("All low similarity pairs filtered successfully")

# Store the similarity scores
filtered_pairs_df.to_csv(
    f'filtered_similarities_{hash}.csv', index=False)
