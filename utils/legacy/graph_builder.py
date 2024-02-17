import os
from py2neo import Graph, Node, Relationship
from recipe_scrapers import scrape_me
import requests
from dotenv import load_dotenv
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()
APP_ID = os.getenv("EDAMAM_APP_ID")
APP_KEY = os.getenv("EDAMAM_APP_KEY")
BASE_URL = os.getenv("EDAMAM_BASE_URL")

# Ensure you have the necessary NLTK data and spacy model
# nltk.download('stopwords')
# nltk.download('wordnet')
# spacy.cli.download("en_core_web_sm")


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

    def extract_key_terms(self, ingredient):
        # Process the ingredient name with spaCy
        # Add a dummy sentence to help spaCy
        ingredient = "I will cook a dish with " + ingredient + "."
        doc = self.nlp(ingredient)
        key_terms = []

        # Define hard-coded allowable non-noun modifiers based on domain
        allowable_modifiers = ["baking", "dried"]

        # Extract any noun terms or compound nouns
        for token in doc:
            if token.dep_ in [
                    'compound', 'ROOT'] and (
                    token.pos_ == 'NOUN' or token.pos_ == 'PROPN'):
                key_terms.append(token.text)
            # only include compound nouns or allowed modifiers
            elif token.dep_ == 'amod':
                if token.text in allowable_modifiers or self.nlp(
                        token.text)[0].pos_ == 'NOUN':
                    key_terms.append(token.text)

        # If empty, return the original ingredient
        if len(key_terms) == 0:
            return ingredient

        # Returning a string that combines the key terms
        return ' '.join(key_terms)

    def preprocess_ingredient(self, ingredient):
        # Normalize case
        ingredient = ingredient.lower()

        # Focus on key terms
        ingredient = self.extract_key_terms(ingredient)

        # Lemmatize to reduce words to their base form
        lemmatizer = WordNetLemmatizer()
        lemmatized = [
            lemmatizer.lemmatize(token)
            for token in ingredient.split(' ')]
        return ' '.join(lemmatized)

    def get_ingredient_vectors(self, ingredients):
        # Convert ingredients to vectors using spaCy
        vectors = [self.nlp(ingredient).vector
                   for ingredient in ingredients]
        return np.array(vectors)

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
            query, normWords=words,
            category=ingredient_data['foodCategory']).data()

        # Then similarity metric filter
        if existing_ingredients:
            preprocessed_ex_ingredients = [
                self.preprocess_ingredient(
                    ex_ingredient['i']['name'])
                for ex_ingredient in existing_ingredients]

            existing_vectors = self.get_ingredient_vectors(
                preprocessed_ex_ingredients)
            new_vector = self.nlp(normalized_name).vector
            similarity = cosine_similarity(
                existing_vectors, [new_vector])
            most_similar_score = np.max(similarity)

            # Tuned to this score
            if most_similar_score > 0.85:
                most_similar = np.argmax(similarity)
                ingredient_node = existing_ingredients[most_similar][
                    'i']
                # Checking sensitivity
                if most_similar_score < 0.95:
                    print(
                        f"Deduped similar ingredient: {ingredient_name} -> {ingredient_node['name']}")
                return ingredient_node

        # Else create a new ingredient node
        ingredient_node = Node(
            "Ingredient",
            name=normalized_name,
            category=ingredient_data['foodCategory'],
            image=ingredient_data['image'])
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

    # Execute the Cypher query
    result = graph_builder.graph.run(query).data()
    node_count = result[0]['nodeCount']

    # # Initialize with base ingredients to avoid de-duping to edge cases
    # ingredients = [
    #     # Meat and Protein
    #     'chicken', 'beef', 'pork', 'fish', 'shrimp', 'tofu', 'tempeh', 'lentils', 'beans', 'chickpeas', 'eggs',
    #     'turkey', 'salmon', 'tuna', 'sausage', 'bacon', 'ham', 'steak', 'ground beef', 'pepperoni', 'crab',
    #     'lobster', 'duck', 'lamb'
    #     # Grains and Flours
    #     'flour', 'rice', 'pasta', 'quinoa', 'oats', 'bread', 'barley', 'couscous', 'bulgur', 'cornmeal', 'wheat germ',
    #     'breadcrumbs', 'polenta', 'farro', 'cereal', 'buckwheat', 'millet', 'amaranth', 'sorghum', 'spelt', 'teff',
    #     # Vegetables
    #     'onion', 'garlic', 'tomato', 'potato', 'carrot', 'bell pepper', 'spinach', 'broccoli', 'mushroom', 'zucchini',
    #     'cucumber', 'celery', 'lettuce', 'cabbage', 'green beans', 'peas', 'corn', 'sweet potato', 'asparagus', 'kale',
    #     'brussels sprouts', 'cauliflower', 'artichoke', 'beet', 'radish', 'turnip', 'eggplant', 'squash', 'pumpkin',
    #     'okra', 'rhubarb', 'fennel', 'leek', 'shallot', 'scallion', 'chives', 'ginger', 'chili pepper', 'jalapeno',
    #     # Fruits
    #     'apple', 'banana', 'orange', 'strawberry', 'blueberry', 'lemon', 'lime', 'grape', 'watermelon', 'pineapple',
    #     'mango', 'kiwi', 'peach', 'pear', 'raspberry', 'blackberry', 'avocado', 'cranberry', 'cherry', 'coconut',
    #     'pomegranate', 'plum', 'fig', 'date', 'guava', 'papaya', 'passion fruit', 'lychee', 'dragonfruit', 'starfruit',
    #     # Dairy and Alternatives
    #     'milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream', 'cream cheese', 'cottage cheese', 'ricotta',
    #     'goat cheese', 'cheddar', 'mozzarella', 'parmesan', 'feta', 'swiss cheese', 'almond milk', 'soy milk',
    #     'coconut milk', 'cashew milk', 'oat milk', 'vegan cheese',
    #     # Herbs and Spices
    #     'salt', 'pepper', 'oregano', 'basil', 'parsley', 'thyme', 'rosemary', 'cumin', 'paprika', 'chili powder',
    #     'cinnamon', 'nutmeg', 'ginger', 'coriander', 'garlic powder', 'onion powder', 'bay leaf', 'turmeric', 'sage',
    #     'dill', 'mustard', 'cayenne', 'curry powder', 'cardamom', 'cloves', 'allspice', 'fennel', 'tarragon',
    # ]

    import time
    # start = time.time()
    # for ingredient in ingredients:
    #     lap = time.time()
    #     graph_builder.build_knowledge_graph_by_ingredient(ingredient)
    #     print(
    #         f"Time to build {ingredient}: {pretty_print_time(time.time() - lap)}")
    # print(
    #     f"Time to build the ingredient graph: {pretty_print_time(time.time() - start)}")

    print("Building the graph for diverse cuisines")

    cuisines = ['Asian', 'Chinese', 'Japanese', 'South East Asian'] + [
        'American', 'Asian', 'British', 'Caribbean',
        'Central Europe', 'Chinese', 'Eastern Europe', 'French',
        'Indian', 'Italian', 'Japanese', 'Kosher', 'Mediterranean',
        'Mexican', 'Middle Eastern', 'Nordic', 'South American',
        'South East Asian']

    # Time this algorithm
    start = time.time()
    while node_count < 6000:
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
