import pytest
from src.graph_builder import GraphBuilder
from src.knowledge_graph import KnowledgeGraph
from neo4j import GraphDatabase

'''
NOTE: This will not work, as a test database is not set up.
'''


@pytest.fixture(scope="module")
def neo4j_driver():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"

    driver = GraphDatabase.driver(uri, auth=(user, password))
    yield driver
    driver.close()


@pytest.fixture(scope="module")
def graph(neo4j_driver):
    # sample data
    sample_data = [
        {"name": "Ingredient1", "category": "Category1"},
        {"name": "Ingredient2", "category": "Category2"},
        {"name": "Ingredient3", "category": "Category3"}
    ]

    # Connect to the Neo4j database using the provided neo4j_driver
    graph = KnowledgeGraph(neo4j_driver)

    # Populate the database with sample data
    for data in sample_data:
        graph.create_node(data["name"], data["category"])


def test_get_ingredient_by_id(graph):
    # Test get_ingredient_by_id method
    ingredient_id = 1
    ingredient = graph.get_ingredient_by_id(ingredient_id)
    assert ingredient is not None


def test_get_ingredient_by_name_fuzzy_search(graph):
    # Test get_ingredient_by_name method (fuzzy search)
    ingredient_name = "fried rice"
    ingredients = graph.get_ingredient_by_name(ingredient_name)
    assert len(ingredients) > 0
