import json
import pickle
from gensim.models import Word2Vec
from gensim.models.phrases import Phrases, Phraser, ENGLISH_CONNECTOR_WORDS
import time
import os
from nltk import WordNetLemmatizer
print("Done importing necessary libraries")

############### Generating Dataset for Word2Vec Training ###############


def generate_training_data():
    start = time.time()

    # Read the JSON file
    file_path = 'train_data/FoodData_Central_sr_legacy_food_json_2021-10-28.json'
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Access the "FoundationFoods" key in the JSON data
    foundation_foods = data["SRLegacyFoods"]

    # Extract the ingredient names
    tokenized_ingredients_from_FDC = [
        food["description"].lower().replace(',', '').split()
        for food in foundation_foods]

    print(
        f"Extracted dataset of length: {len(tokenized_ingredients_from_FDC)}")

    # Read the text file
    file_path = 'train_data/usda_food_items.txt'

    # Read the content of the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Extract ingredient names from each line
    tokenized_ingredients_from_usda = [
        line.strip().split('~^~')[2].lower().replace(',', '').split()
        for line in lines]

    print(
        f"Extracted dataset of length: {len(tokenized_ingredients_from_usda)}")

    # Read the json file
    file_path = 'train_data/recipes.json'

    with open(file_path, 'r') as file:
        data = json.load(file)

    # Extract the steps and ingredients from the JSON data
    all_steps = [recipe["steps"] for recipe in data]
    all_ingredients = [recipe["ingredients"] for recipe in data]
    tokenized_ingredients_from_kaggle = []

    for recipe_steps, recipe_ingredients in zip(
            all_steps, all_ingredients):
        tokenized_steps = [step.lower().replace(',', '').split()
                           for step in recipe_steps]
        tokenized_steps = [item
                           for sublist in tokenized_steps for item in
                           sublist]
        tokenized_ingredients = [
            ingredient.lower().replace(',', '').split()
            for ingredient in recipe_ingredients]
        tokenized_ingredients = [item
                                 for sublist in tokenized_ingredients
                                 for item in sublist]

        tokenized_ingredients_from_kaggle.append(
            tokenized_steps + tokenized_ingredients)

    # Combine the two lists of tokenized ingredients
    print(
        f"Extracted dataset of length: {len(tokenized_ingredients_from_kaggle)}")

    # Combine the lists of tokenized ingredients
    tokens = tokenized_ingredients_from_FDC + \
        tokenized_ingredients_from_usda + tokenized_ingredients_from_kaggle
    print(f"Generated net dataset of length: {len(tokens)}")

    def build_phrases(sentences):
        phrases = Phrases(sentences,
                          min_count=1,
                          threshold=2,
                          progress_per=1000,
                          connector_words=ENGLISH_CONNECTOR_WORDS
                          )
        return Phraser(phrases)

    # Apply the phrases to the data
    phrase_model = build_phrases(tokens)

    phrase_model.save("phrase_model.txt")

    # Apply the phrases to your tokens
    tokenized_phrases = phrase_model[tokens]

    with open('tokenized_phrases.pkl', 'wb') as f:
        pickle.dump(tokenized_phrases, f)

    print("Done generating training dataset in ",
          time.time() - start, "seconds")


if __name__ == "__main__":
    if "tokenized_phrases.pkl" not in os.listdir():
        generate_training_data()
     # Load the tokenized phrases
    with open('tokenized_phrases.pkl', 'rb') as f:
        tokenized_phrases = pickle.load(f)

    #################### Training the Word2Vec Model #######################

    # Time training
    start = time.time()

    model = Word2Vec(sentences=tokenized_phrases, vector_size=200,
                     window=10, min_count=1, workers=4)
    print("Done training the Word2Vec model in ",
          time.time() - start, "seconds")

    # Save the trained model
    model.save("phrases_ingredient_word2vec.model")
