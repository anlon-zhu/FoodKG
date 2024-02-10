import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re

# Ensure you have the necessary NLTK data and spacy model
# nltk.download('stopwords')
# nltk.download('wordnet')
# spacy.cli.download("en_core_web_sm")

nlp = spacy.load("en_core_web_sm", exclude=["ner", "textcat"])


def get_ingredient_vectors(ingredients):
    # Convert ingredients to vectors using spaCy
    vectors = [nlp(ingredient).vector for ingredient in ingredients]
    return np.array(vectors)


def extract_key_terms(ingredient):
    # Process the ingredient name with spaCy
    doc = nlp(ingredient)
    key_terms = []

    # Define hard-coded allowable non-noun modifiers based on domain
    allowable_modifiers = ["baking", "dried"]

    # Extract any noun terms or compound nouns
    for token in doc:
        if token.dep_ in [
                'compound', 'ROOT'] and (
                token.pos_ == 'NOUN' or token.pos_ == 'PROPN'):
            print('token noun', token.text, token.pos_, token.dep_)
            key_terms.append(token.text)
        # only include compound nouns or allowed modifiers
        elif token.dep_ == 'amod':
            if token.text in allowable_modifiers or nlp(
                    token.text)[0].pos_ == 'NOUN':
                key_terms.append(token.text)

    # If empty, return the original ingredient
    if len(key_terms) == 0:
        return ingredient

    # Returning a string that combines the key terms
    return ' '.join(key_terms)


def preprocess_ingredient(ingredient):
    # Normalize case
    ingredient = ingredient.lower()

    # Focus on key terms
    ingredient = extract_key_terms(ingredient)

    # Lemmatize to reduce words to their base form
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(token)
                  for token in ingredient.split(' ')]
    return ' '.join(lemmatized)


# Example usage
ingredients = [
    'tomato paste', 'diced tomatoes', 'tomato sauce', 'dried oregano',
    'dried basil', 'garlic powder', 'chicken-thighs', 'onion powder',
    'self-raising flour', 'baking powder', 'baking soda',
    'freshly squeezed lemon juice', 'lemon juice', 'cup of water',
    'cup of coffee', 'tomato of china']
test_ingredient = 'baking powder'

for ingredient in ingredients:
    print(
        f"Original: {ingredient} -> Key Terms: {extract_key_terms(ingredient)}")

preprocessed_ingredients = [preprocess_ingredient(
    ingredient) for ingredient in ingredients]

new_preprocessed = preprocess_ingredient(test_ingredient)

print('pre', preprocessed_ingredients)
print('new pre', new_preprocessed)

# existing_vectors = get_ingredient_vectors(preprocessed_ingredients)
# new_vector = nlp(new_preprocessed).vector

# similarity = cosine_similarity(
#     existing_vectors, [new_vector])
# most_similar_score = np.max(similarity)
# print('best score', most_similar_score)

# # print similarity and ingredient next to each other
# print('similarity')
# for similarity, ingredients in zip(similarity, ingredients):
#     print(similarity, ingredients)
# if most_similar_score > 0.9:
#     most_similar = np.argmax(similarity)
#     print('most similar idx', most_similar)
#     print('most similar ingredient', ingredients[most_similar])

# Process clusters to unify ingredient names in your graph...
