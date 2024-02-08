import os
from py2neo import Graph, Node, Relationship
from recipe_scrapers import scrape_me
import requests
from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("EDAMAM_APP_ID")
APP_KEY = os.getenv("EDAMAM_APP_KEY")
BASE_URL = os.getenv("EDAMAM_BASE_URL")


class GraphBuilder:
    '''
    Class for building/updating a knowledge graph of recipes and ingredients.
    This is separate from the class for querying the knowledge graph.
    '''

    def __init__(self, uri, user, password):
        self.graph = Graph(uri, auth=(user, password))

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

    def get_or_create_ingredient_node(self, ingredient_data):
        ingredient_name = ingredient_data['food']
        ingredient_node = self.graph.nodes.match(
            "Ingredient", name=ingredient_name).first()
        if not ingredient_node:
            ingredient_node = Node(
                "Ingredient", name=ingredient_name,
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
                totalTime = scraper.total_time()
            except:
                totalTime = None

            recipe_node = Node(
                "Recipe", name=recipe['label'],
                url=url,
                image=recipe['image'],
                cuisineType=recipe['cuisineType'],
                totalTime=totalTime,
            )
            self.graph.create(recipe_node)
        return recipe_node

    def create_relationships(self, recipe_node, ingredient_node):
        self.graph.create(
            Relationship(
                recipe_node, "CONTAINS", ingredient_node,
                quantity=ingredient_node['quantity'],
                measure=ingredient_node['measure']))
        self.graph.create(
            Relationship(ingredient_node, "PART_OF", recipe_node,
                         quantity=ingredient_node['quantity'],
                         measure=ingredient_node['measure']))

    def create_recipe_node_with_ingredients(self, recipe_data):
        recipe_node = self.get_or_create_recipe_node(recipe_data)

        for ingredient in recipe_data['recipe']['ingredients']:
            ingredient_node = self.get_or_create_ingredient_node(
                ingredient)
            self.create_relationships(recipe_node, ingredient_node)

    def build_knowledge_graph(self):
        cuisines = [
            'American', 'Asian', 'British', 'Caribbean',
            'Central Europe', 'Chinese', 'Eastern Europe', 'French',
            'Indian', 'Italian', 'Japanese', 'Kosher', 'Mediterranean',
            'Mexican', 'Middle Eastern', 'Nordic', 'South American',
            'South East Asian']

        for cuisine in cuisines:
            recipes = self.search_recipes_by_cuisine(cuisine)
            print(f"Found {len(recipes)} recipes for {cuisine}")

            for recipe in recipes:
                print(
                    f"Building recipe node for {recipe['recipe']['label']}")
                self.create_recipe_node_with_ingredients(recipe)


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
    node_count = 2000

    while node_count < 5000:
        print(f"Current node count: {node_count}")
        graph_builder.build_knowledge_graph()
        result = graph_builder.graph.run(query).data()
        node_count = result[0]['nodeCount']
