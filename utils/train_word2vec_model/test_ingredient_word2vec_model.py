from gensim.models import Word2Vec
import spacy
from nltk.stem import WordNetLemmatizer
from gensim.models.phrases import Phrases, Phraser

nlp = spacy.load("en_core_web_sm", exclude=["textcat"])

# Load the trained Word2Vec model
model = Word2Vec.load("phrases_ingredient_word2vec.model")
phrase_model = Phraser.load("phrase_model.txt")


def get_similarity_score(word1, word2):
    # Tokenize the input words and generate phrases
    tokens_word1 = word1.split()
    tokens_word2 = word2.split()

    tokens_word1 = phrase_model[tokens_word1]
    tokens_word2 = phrase_model[tokens_word2]

    similarity_scores = []

    for token1 in tokens_word1:
        for token2 in tokens_word2:
            # Must have at least one equivalent token to compare
            if token1 == token2:
                similarity_scores.append(1)
            elif token1 in model.wv.key_to_index and token2 in model.wv.key_to_index:
                similarity_score = model.wv.similarity(token1, token2)
                similarity_scores.append(similarity_score)
            else:
                continue
    # Average similarity scores
    return sum(
        similarity_scores) / len(similarity_scores) if similarity_scores else 0


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
    ("chicken breast", "chicken thigh"),
    ("reduced-sodium soy sauce", "soy sauce"),
    ("tomato", "tomato sauce"),
    ("tomato", "tomato paste"),
    ("tomato", "tomato ketchup"),
    ("tomato", "tomato juice"),
    ("tomato", "tomato puree"),
    ("diced tomatoes", "tomato soup"),
    ("tomato sauce ", "tomato paste"),
    ("dried oregano", "fresh oregano"),
    ("chicken broth", "chicken stock"),
    ("ground beef", "ground turkey"),
    ("whole milk", "skim milk"),
    ("olive oil", "vegetable oil"),
    ("white sugar", "brown sugar"),
    ("all-purpose flour", "whole wheat flour"),
    ("parmesan cheese", "pecorino romano cheese"),
    ("white rice", "brown rice"),
    ("lemon juice", "lime juice"),
    ("honey", "maple syrup"),
    ("cilantro", "parsley"),
    ("red onion", "yellow onion"),
    ("bell pepper", "jalapeno pepper"),
    ("dark chocolate", "milk chocolate"),
    ("basil leaves", "mint leaves"),
    ("ground cinnamon", "ground nutmeg"),
    ("ground black pepper", "white pepper"),
    ("balsamic vinegar", "red wine vinegar"),
    ("chicken sausage", "pork sausage"),
    ("baby spinach", "arugula"),
    ("cottage cheese", "ricotta cheese")
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
