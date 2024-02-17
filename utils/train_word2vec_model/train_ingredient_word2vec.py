import json
from gensim.models import Word2Vec
import time

print("Done importing necessary libraries")

############### Generating Dataset for Word2Vec Training ###############
start = time.time()
# # Read the JSON file
file_path = 'train_data/FoodData_Central_sr_legacy_food_json_2021-10-28.json'
with open(file_path, 'r') as file:
    data = json.load(file)

# Access the "FoundationFoods" key in the JSON data
foundation_foods = data["SRLegacyFoods"]

# Extract the ingredient names
tokenized_ingredients = [
    food["description"].lower().replace(',', '').split()
    for food in foundation_foods]

print(f"Extracted dataset of length: {len(tokenized_ingredients)}")

# Read the text file
file_path = 'train_data/usda_food_items.txt'

# Read the content of the file
with open(file_path, 'r') as file:
    lines = file.readlines()

# Extract ingredient names from each line
tokenized_ingredients_from_usda = [
    line.strip().split('~^~')[2].lower().replace(',', '').split()
    for line in lines]


# Combine the two lists of tokenized ingredients
tokenized_ingredients.extend(tokenized_ingredients_from_usda)
print(f"Generated net dataset of length: {len(tokenized_ingredients)}")

print("Done generating training dataset in ",
      time.time() - start, "seconds")

#################### Training the Word2Vec Model #######################
# Time training
start = time.time()

model = Word2Vec(sentences=tokenized_ingredients,
                 vector_size=200, window=10, min_count=1, workers=4)
print("Done training the Word2Vec model in ",
      time.time() - start, "seconds")
# Save the trained model
model.save("ingredient_word2vec.model")
