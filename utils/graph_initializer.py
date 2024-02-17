import pandas as pd
import ast
from py2neo import Graph, Node, Subgraph, Relationship
import csv
import os
from dotenv import load_dotenv
import time
from gensim.models import Word2Vec

load_dotenv()

# Connect to Neo4j
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
graph = Graph(uri, auth=(username, password))
graph.run(
    "CREATE INDEX IF NOT EXISTS FOR (i:Ingredient) ON (i.name)").evaluate()

# Load the trained Word2Vec model
model = Word2Vec.load("ingredient_word2vec.model")

# Load similarity matrix
filename = "filtered_similarities_1708123481.csv"
similarity_matrix = pd.read_csv(filename, index_col=0)


def check_similarity(ingredient1, ingredient2):
    '''
    Check if two ingredients are similar based on the similarity matrix
    '''
    try:
        similarity_value = similarity_matrix.loc[ingredient1,
                                                 ingredient2]
    except KeyError:
        try:
            similarity_value = similarity_matrix.loc[ingredient2,
                                                     ingredient1]
        except KeyError:
            similarity_value = 0.0

    return similarity_value


def import_data_from_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        start = time.time()
        for index, row in enumerate(reader, 1):
            # Parse strings representing lists into actual lists
            row['ingredients'] = ast.literal_eval(row['ingredients'])
            row['directions'] = ast.literal_eval(row['directions'])
            row['NER'] = ast.literal_eval(row['NER'])

            print(row['title'])
            recipe_node = Node(
                "Recipe", name=row['title'],
                instructions=row['directions'],
                ingredient_quantities=row['ingredients'],
                source=row['source'],
                link=row['link'])

            ingredients_nodes = []
            relationships = []

            for ingredient in row['NER']:
                ingredient_name = ingredient.strip().lower()
                ingredient_node = Node(
                    "Ingredient", name=ingredient_name)

                # Check if ingredient already exists in the graph
                existing_ingredients = graph.nodes.match(
                    "Ingredient", name=ingredient_name)
                if existing_ingredients:
                    for existing_ingredient in existing_ingredients:
                        # Check similarity with existing ingredients
                        similarity = check_similarity(
                            ingredient_name,
                            existing_ingredient['name'])
                        if similarity > 0.95:
                            # Map the new ingredient onto the existing one
                            ingredient_node = existing_ingredient
                            break  # Stop checking other existing ingredients
                        elif similarity > 0.85:
                            # Create similar relationship
                            relationships.append(
                                Relationship(
                                    ingredient, "SIMILAR_TO",
                                    existing_ingredient))
                            relationships.append(
                                Relationship(
                                    existing_ingredient, "SIMILAR_TO",
                                    ingredient))

                ingredients_nodes.append(ingredient_node)
                relationships.append(
                    Relationship(
                        recipe_node, "CONTAINS",
                        ingredient_node))
                relationships.append(
                    Relationship(
                        ingredient_node, "PART_OF",
                        recipe_node))

            graph.merge(recipe_node, "Recipe", "name")
            [graph.merge(ingredient_node, "Ingredient", "name")
             for ingredient_node in ingredients_nodes]
            [graph.merge(relationship)
             for relationship in relationships]

            if index % 100 == 0:
                print(
                    f"Imported {index} recipes in {time.time() - start} seconds")
                start = time.time()


if __name__ == "__main__":
    csv_file = "dataset/full_dataset.csv"
    net_start = time.time()
    import_data_from_csv(csv_file)
    print("Data imported successfully in",
          time.time() - net_start, "seconds.")
