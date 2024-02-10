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
# spacy.cli.download("en_core_web_md")

nlp = spacy.load("en_core_web_md")


def get_ingredient_vectors(ingredients):
    # Convert ingredients to vectors using spaCy
    vectors = [nlp(ingredient).vector for ingredient in ingredients]
    return np.array(vectors)


def extract_key_terms(ingredient):
    # Process the ingredient name with spaCy
    doc = nlp(ingredient)
    key_terms = []

    # Extract nouns and proper nouns as they are likely to be key ingredients
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN', 'VERB']:
            key_terms.append(token.text)

    # Returning a string that combines the key terms
    return ' '.join(key_terms)


def preprocess_ingredient(ingredient):
    # Normalize case
    ingredient = ingredient.lower()

    # Focus on key terms
    ingredient = extract_key_terms(ingredient)

    # Tokenize and remove stopwords
    tokens = [token for token in ingredient.split()
              if token not in stopwords.words('english')]

    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(token) for token in tokens]

    return ' '.join(lemmatized)


# Example usage
ingredients = [
    'chicken-thighs', 'onion powder', 'self-raising flour',
    'baking powder', 'freshly squeezed lemon juice', 'lemon juice']
test_ingredient = 'baking powder'

for ingredient in ingredients:
    print(
        f"Original: {ingredient} -> Key Terms: {extract_key_terms(ingredient)}")

preprocessed_ingredients = [preprocess_ingredient(
    ingredient) for ingredient in ingredients]

new_preprocessed = preprocess_ingredient(test_ingredient)

print('pre', preprocessed_ingredients)
print('new pre', new_preprocessed)

existing_vectors = get_ingredient_vectors(preprocessed_ingredients)
new_vector = nlp(new_preprocessed).vector

similarity = cosine_similarity(
    existing_vectors, [new_vector])
most_similar_score = np.max(similarity)
print('best score', most_similar_score)

# print similarity and ingredient next to each other
print('similarity')
for similarity, ingredients in zip(similarity, ingredients):
    print(similarity, ingredients)
if most_similar_score > 0.9:
    most_similar = np.argmax(similarity)
    print('most similar idx', most_similar)
    print('most similar ingredient', ingredients[most_similar])

# Process clusters to unify ingredient names in your graph...
