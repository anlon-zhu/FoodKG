from gensim.models import Word2Vec
import spacy
from nltk.stem import WordNetLemmatizer

nlp = spacy.load("en_core_web_sm", exclude=["textcat"])

# Load the trained Word2Vec model
model = Word2Vec.load("ingredient_word2vec.model")


def get_similarity_score(word1, word2):
    # Tokenize the input words
    viable_flag = False
    tokens_word1 = word1.split()
    tokens_word2 = word2.split()

    # Compute similarity between all token pairs
    similarity_scores = []
    for token1 in tokens_word1:
        for token2 in tokens_word2:
            # Must have at least one equivalent token to compare
            if token1 == token2:
                similarity_scores.append(1)
                viable_flag = True
            elif token1 in model.wv.key_to_index and token2 in model.wv.key_to_index:
                similarity_score = model.wv.similarity(token1, token2)
                similarity_scores.append(similarity_score)
            else:
                # If either token is not in the vocabulary, skip
                continue

    # Average similarity scores
    return sum(
        similarity_scores) / len(similarity_scores) if viable_flag else 0


def preprocess_ingredient(ingredient):
    # Normalize case
    ingredient = ingredient.lower()

    # Lemmatize to reduce words to their base form
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(token)
                  for token in ingredient.split(' ')]
    return ' '.join(lemmatized)


# Main test
# Example of word similarity evaluation
word_pairs = [
    ("chicken", "beef"),
    ("pork", "beef"),
    ("cheese", "milk"),
    ("tomato", "potato"),
    ("chicken thigh", "chicken breast"),
    ("chicken thigh", "potato"),
    ("chicken breast", "beef steak"),
    ("chicken breast", "chicken stock"),
    ("chicken breast", "skinless chicken breast"),
    ("chicken stock", "chicken broth"),
    ("chicken stock", "beef stock"),
    ("chicken stock", "tomato sauce"),
    ("tomatoes", "diced tomatoes"),
    ("tomato sauce", "tomato paste"),
    ("tomato sauce", "diced tomatoes"),
    ("tomato paste", "diced tomatoes"),
    ("tomato paste", "tomato sauce"),
    ("tomato paste", "tomato"),
    ("dried oregano", "dried basil"),
    ("dried oregano", "garlic powder"),
    ("dried basil", "garlic powder"),
    ("dried basil", "onion powder"),
    ("garlic powder", "onion powder"),
    ("baking powder", "baking soda"),
    ("baking powder", "self-raising flour"),
    ("baking soda", "self-raising flour"),
    ["freshly squeezed lemon juice", "lemon juice"],
    ["freshly squeezed lemon juice", "cup of water"],
    ["freshly squeezed lemon juice", "cup of coffee"],
    ["lemon juice", "cup of water"],
    ["lemon juice", "cup of coffee"],
    ["cup of water", "cup of coffee"],
    ["flour", "self-raising flour"]
]

averages = []

for word1, word2 in word_pairs:
    word1 = preprocess_ingredient(word1)
    word2 = preprocess_ingredient(word2)
    similarity = get_similarity_score(word1, word2)
    averages.append((word1, word2, similarity))

# Print the similarity scores
averages.sort(key=lambda x: x[2], reverse=True)
for word1, word2, similarity in averages:
    print(
        f"Similarity score between '{word1}' and '{word2}': {similarity}")
