import os
from py2neo import Graph, Node, Relationship
from recipe_scrapers import scrape_me
import requests
from dotenv import load_dotenv
from nltk.stem import WordNetLemmatizer
import spacy
import numpy as np
from gensim.models import Word2Vec
from gensim.models.phrases import Phrases, Phraser

import time

load_dotenv()
APP_ID = os.getenv("EDAMAM_APP_ID")
APP_KEY = os.getenv("EDAMAM_APP_KEY")
BASE_URL = os.getenv("EDAMAM_BASE_URL")


# Load your Word2Vec model
model = Word2Vec.load("phrases_ingredient_word2vec.model")
phrase_model = Phraser.load("phrase_model.txt")
print("Model loaded successfully")


class GraphBuilder:
    '''
    Class for building/updating a knowledge graph of recipes and ingredients.
    This is separate from the class for querying the knowledge graph and should
    only be run once.
    '''

    def __init__(self, uri, user, password):
        self.graph = Graph(uri, auth=(user, password))
        self.nlp = spacy.load(
            "en_core_web_sm", exclude=["ner", "textcat"])
        self.avoided_dedupes = []
        self.dodgy_dedupes = []

    def search_recipes_by_ingredient(self, ingredient):
        endpoint = f'{BASE_URL}/'
        params = {
            'type': 'public',
            'q': ingredient,
            'app_id': APP_ID,
            'app_key': APP_KEY
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        return data.get('hits', [])

    def search_recipes_by_cuisine(self, cuisine):
        endpoint = f'{BASE_URL}/'
        params = {
            'type': 'public',
            'cuisineType': cuisine,
            'random': 'true',
            'app_id': APP_ID,
            'app_key': APP_KEY
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        return data.get('hits', [])

    def preprocess_ingredient(self, ingredient):
        # Normalize case
        ingredient = ingredient.lower()

        # Lemmatize to reduce words to their base form
        lemmatizer = WordNetLemmatizer()
        lemmatized = [
            lemmatizer.lemmatize(token)
            for token in ingredient.split(' ')]
        return ' '.join(lemmatized)

    def calculate_similarity(self, word1, word2):
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
                    similarity_score = model.wv.similarity(
                        token1, token2)
                    similarity_scores.append(similarity_score)
                else:
                    continue
        # Average similarity scores
        return sum(
            similarity_scores) / len(similarity_scores) if similarity_scores else 0

    def get_or_create_ingredient_node(self, ingredient_data):
        ingredient_name = ingredient_data['food']
        normalized_name = self.preprocess_ingredient(ingredient_name)
        words = normalized_name.split()

        # First, check for exact match
        query = """
        MATCH (i:Ingredient)
        WHERE toLower(i.name) = $name
        RETURN i
        """
        matching_ingredient = self.graph.run(
            query, name=normalized_name).data()

        if matching_ingredient:
            return matching_ingredient[0]['i']

        # Then, similarity match for ingredients with any common words
        query = """
        MATCH (i:Ingredient)
        WHERE any(word IN $normWords WHERE toLower(i.name) CONTAINS word)
        RETURN i
        """

        existing_ingredients = self.graph.run(
            query, normWords=words).data()

        # Then similarity metric filter
        if existing_ingredients:
            preprocessed_ex_ingredients = [
                self.preprocess_ingredient(
                    ex_ingredient['i']['name'])
                for ex_ingredient in existing_ingredients]

            similarity = [
                self.calculate_similarity(
                    normalized_name, ex_ingredient)
                for ex_ingredient in preprocessed_ex_ingredients]

            most_similar_score = np.max(similarity)
            most_similar = np.argmax(similarity)

            # Hyperparameter that is manually tuned
            if most_similar_score > 0.87:
                ingredient_node = existing_ingredients[most_similar][
                    'i']
                # Conditional check for tuning sensitivity
                if most_similar_score < 0.95:
                    self.dodgy_dedupes.append(
                        (ingredient_name, ingredient_node['name']))
                    print(
                        f"Deduped similar ingredient: {ingredient_name} -> {ingredient_node['name']}")
                return ingredient_node
            # Conditional check for tuning specificity
            elif most_similar_score > 0.8:
                self.avoided_dedupes.append(
                    (ingredient_name, existing_ingredients[most_similar]['i']['name']))
        # Else create a new ingredient node
        ingredient_node = Node(
            "Ingredient",
            name=normalized_name,
            category=ingredient_data['foodCategory'])
        self.graph.create(ingredient_node)

        return ingredient_node

    def force_create_ingredient_node(self, ingredient_data):
        ingredient_name = ingredient_data['food']
        normalized_name = self.preprocess_ingredient(ingredient_name)

        ingredient_node = Node(
            "Ingredient",
            name=normalized_name,
            category=ingredient_data['foodCategory'])
        self.graph.create(ingredient_node)

        return ingredient_node

    def get_or_create_recipe_node(self, recipe_data):
        recipe = recipe_data['recipe']
        recipe_node = self.graph.nodes.match(
            "Recipe", name=recipe['label']).first()
        if not recipe_node:
            url = recipe['url']
            try:
                scraper = scrape_me(url, wild_mode=True)
                instructions = scraper.instructions_list()
                totalTime = scraper.total_time()
            except:
                return None

            recipe_node = Node(
                "Recipe", name=recipe['label'],
                url=url,
                image=recipe['image'],
                cuisineType=recipe['cuisineType'],
                totalTime=totalTime,
                instructions=instructions,
            )
            self.graph.create(recipe_node)
        return recipe_node

    def create_relationships(
            self, recipe_node, ingredient_node, quantity, measure):
        self.graph.create(
            Relationship(
                recipe_node, "CONTAINS", ingredient_node,
                quantity=quantity,
                measure=measure))
        self.graph.create(
            Relationship(ingredient_node, "PART_OF", recipe_node,
                         quantity=quantity,
                         measure=measure))

    def create_recipe_node_with_ingredients(self, recipe_data):
        recipe_node = self.get_or_create_recipe_node(recipe_data)
        # We only want recipe nodes with instructions
        if not recipe_node:
            return

        for ingredient in recipe_data['recipe']['ingredients']:
            ingredient_node = self.get_or_create_ingredient_node(
                ingredient)
            quantity = ingredient['quantity']
            measure = ingredient['measure']
            self.create_relationships(
                recipe_node, ingredient_node, quantity, measure)

    def build_knowledge_graph_by_cuisine(self, cuisine):
        recipes = self.search_recipes_by_cuisine(cuisine)
        print(f"Found {len(recipes)} recipes for {cuisine}")

        for recipe in recipes:
            print(
                f"Building recipe node for {recipe['recipe']['label']}")
            self.create_recipe_node_with_ingredients(recipe)

    def build_knowledge_graph_by_ingredient(self, ingredient):
        recipes = self.search_recipes_by_ingredient(ingredient)
        print(f"Found {len(recipes)} recipes for {ingredient}")

        for recipe in recipes:
            print(
                f"Building recipe node for {recipe['recipe']['label']}")
            self.create_recipe_node_with_ingredients(recipe)


def pretty_print_time(seconds):
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds / 60} minutes"
    else:
        return f"{seconds / 3600} hours"


if __name__ == "__main__":

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    graph_builder = GraphBuilder(uri, user, password)

    # Define your Cypher query to count nodes
    query = """
    MATCH (n)
    RETURN count(n) AS nodeCount
    """

    while True:
        # Execute the Cypher query
        result = graph_builder.graph.run(query).data()
        node_count = result[0]['nodeCount']

        if node_count > 5000:
            break

        # # Define initialized ingredients
        # food_categories = {
        #     'Meat and Protein':
        #     ['chicken', 'beef', 'pork', 'fish', 'shrimp', 'tofu', 'tempeh',
        #      'lentils', 'beans', 'chickpeas', 'eggs', 'turkey', 'salmon',
        #      'tuna', 'sausage', 'bacon', 'ham', 'steak', 'ground beef',
        #      'pepperoni', 'crab', 'lobster', 'duck', 'lamb'],
        #     'Grains':
        #     ['flour', 'noodles', 'rice', 'pasta', 'quinoa', 'oats', 'bread',
        #      'barley', 'couscous', 'bulgur', 'cornmeal', 'wheat germ',
        #      'breadcrumbs', 'polenta', 'farro', 'cereal', 'buckwheat',
        #      'millet', 'amaranth', 'sorghum', 'spelt', 'teff'],
        #     'Vegetables':
        #     ['spring onion', 'onion', 'garlic', 'tomato', 'potato', 'carrot',
        #      'bell pepper', 'spinach', 'broccoli', 'mushroom', 'zucchini',
        #      'cucumber', 'celery', 'lettuce', 'cabbage', 'green beans',
        #      'peas', 'corn', 'sweet potato', 'asparagus', 'kale',
        #      'brussels sprouts', 'cauliflower', 'artichoke', 'beet',
        #      'radish', 'turnip', 'eggplant', 'squash', 'pumpkin', 'okra',
        #      'rhubarb', 'fennel', 'leek', 'shallot', 'scallion', 'chives',
        #      'ginger', 'chili pepper', 'jalapeno'],
        #     'Fruits':
        #     ['apple', 'banana', 'orange', 'strawberry', 'blueberry',
        #      'lemon', 'lime', 'grape', 'watermelon', 'pineapple', 'mango',
        #      'kiwi', 'peach', 'pear', 'raspberry', 'blackberry', 'avocado',
        #      'cranberry', 'cherry', 'coconut', 'pomegranate', 'plum', 'fig',
        #      'date', 'guava', 'papaya', 'passion fruit', 'lychee',
        #      'dragonfruit', 'starfruit'],
        #     'Dairy and Alternatives':
        #     ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream',
        #      'cream cheese', 'cottage cheese', 'ricotta', 'goat cheese',
        #      'cheddar', 'mozzarella', 'parmesan', 'feta', 'swiss cheese',
        #      'almond milk', 'soy milk', 'coconut milk', 'cashew milk',
        #      'oat milk', 'vegan cheese'],
        #     'Herbs and Spices':
        #     ['salt', 'pepper', 'oregano', 'basil', 'parsley', 'thyme',
        #      'sesame seeds', 'rosemary', 'cumin', 'paprika', 'chili powder',
        #      'cinnamon', 'nutmeg', 'ginger', 'coriander', 'garlic powder',
        #      'onion powder', 'bay leaf', 'turmeric', 'sage', 'dill',
        #      'mustard', 'cayenne', 'curry powder', 'cardamom', 'cloves',
        #      'allspice', 'fennel', 'tarragon'],
        #     'Sauces':
        #     ['soy sauce', 'vinegar', 'black vinegar', 'rice vinegar', 'fish sauce',
        #      'Worcestershire sauce', 'teriyaki sauce', 'hot sauce',
        #      'barbecue sauce', 'ketchup', 'mayonnaise', 'mustard', 'relish',
        #      'salsa', 'tahini', 'hoisin sauce', 'sriracha'],
        #     'Oils': ['oil', 'olive oil', 'coconut oil', 'sesame oil'],
        #     'Nuts':
        #     ['peanut butter', 'almonds', 'walnuts', 'cashews', 'peanuts',
        #      'pecans', 'pistachios', 'macadamia nuts', 'hazelnuts',
        #      'Brazil nuts'],
        #     'Juice':
        #     ['orange juice', 'apple juice', 'grape juice',
        #      'cranberry juice', 'pineapple juice', 'tomato juice',
        #      'lemon juice', 'lime juice', 'vegetable juice', 'prune juice'],
        #     'Sweeteners':
        #     ['sugar', 'brown sugar', 'honey', 'maple syrup', 'agave nectar',
        #      'molasses', 'artificial sweeteners'],
        #     'Canned Foods':
        #     ['canned beans', 'canned tomatoes', 'canned tuna',
        #      'canned salmon', 'canned vegetables', 'canned fruit',
        #      'canned soup', 'canned broth', 'canned coconut milk',
        #      'canned pumpkin', 'canned olives', 'canned corn',
        #      'canned chickpeas'], }

        # start = time.time()
        # # Initialize some ingredients
        # for category, ingredients_list in food_categories.items():
        #     for ingredient in ingredients_list:
        #         graph_builder.force_create_ingredient_node(
        #             {'food': ingredient, 'foodCategory': category})
        # print(
        #     f"Time to build the ingredients: {pretty_print_time(time.time() - start)}")

        print("Building the graph for diverse cuisines")

        cuisines = [
            'Asian', 'Chinese', 'Japanese', 'South East Asian'] + [
            'American', 'Asian', 'British', 'Caribbean',
            'Central Europe', 'Chinese', 'Eastern Europe', 'French',
            'Indian', 'Italian', 'Japanese', 'Kosher', 'Mediterranean',
            'Mexican', 'Middle Eastern', 'Nordic', 'South American',
            'South East Asian']

        # Time this algorithm
        start = time.time()
        for cuisine in cuisines:
            # get time to build each cuisine as a lap
            lap = time.time()
            graph_builder.build_knowledge_graph_by_cuisine(cuisine)
            print(
                f"Time to build {cuisine}: {pretty_print_time(time.time() - lap)}")
        node_count = graph_builder.graph.run(query).data()[
            0]['nodeCount']
        print(f"Current node count: {node_count}")
        print(
            f"Time to build the cuisine graph: {pretty_print_time(time.time() - start)}")

    # Write the avoided and dodgy dedupes to a file
    with open("dodgy_dedupes.txt", "w") as file:
        for ingredient in graph_builder.dodgy_dedupes:
            file.write(f"{ingredient[0]} -> {ingredient[1]}\n")
    with open("avoided_dedupes.txt", "w") as file:
        for ingredient in graph_builder.avoided_dedupes:
            file.write(f"{ingredient[0]} -> {ingredient[1]}\n")
