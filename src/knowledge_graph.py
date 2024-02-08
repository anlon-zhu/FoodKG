from py2neo import Graph, NodeMatcher, RelationshipMatcher
import re


class KnowledgeGraph:
    '''
    Knowledge graph class for querying the knowledge graph of recipes from
    the Neo4j database from which the graph is intialized.
    '''

    def __init__(self, uri, user, password):
        self.graph = Graph(uri, auth=(user, password))
        self.node_matcher = NodeMatcher(self.graph)
        self.rel_matcher = RelationshipMatcher(self.graph)

    def get_ingredient_count(self):
        return self.graph.evaluate(
            "MATCH (i:Ingredient) RETURN COUNT(i)")

    def get_recipe_count(self):
        return self.graph.evaluate("MATCH (r:Recipe) RETURN COUNT(r)")

    def get_ingredient_by_id(self, ingredient_id):
        return self.node_matcher.match(
            "Ingredient", id=ingredient_id).first()

    def get_ingredients_by_name(self, ingredient_name):
        return list(
            self.node_matcher.match(
                "Ingredient", name=ingredient_name))

    def get_ingredients_by_name_fuzzy(self, ingredient_name):
        '''
        Returns a list of ingredients whose name fuzzy matches the query.
        '''
        pattern = f".*{ingredient_name}.*"
        ingredients = list(self.node_matcher.match("Ingredient"))
        matched_ingredients = [
            ingredient for ingredient in ingredients
            if re.match(pattern, ingredient['name'],
                        re.IGNORECASE)]
        return matched_ingredients

    def get_ingredients_by_category(self, category):
        return list(
            self.node_matcher.match(
                "Ingredient", category=category))

    def get_recipe_by_id(self, recipe_id):
        return self.node_matcher.match("Recipe", id=recipe_id).first()

    def get_recipe_by_url(self, recipe_url):
        return self.node_matcher.match("Recipe", url=recipe_url).first()

    def get_recipes_by_name(self, recipe_name):
        return list(self.node_matcher.match("Recipe", name=recipe_name))

    def get_recipes_by_name_fuzzy(self, recipe_name):
        '''
        Returns a list of recipes whose name fuzzy matches the query.
        '''
        pattern = f".*{recipe_name}.*"
        recipes = list(self.node_matcher.match("Recipe"))
        matched_recipes = [recipe for recipe in recipes if re.match(
            pattern, recipe['name'], re.IGNORECASE)]
        return matched_recipes

    def get_recipes_by_cuisine(self, cuisine_type):
        return list(
            self.node_matcher.match(
                "Recipe", cuisineType=cuisine_type))

    def get_recipes_with_total_time_less_than(self, max_time):
        query = f"""
        MATCH (r:Recipe)
        WHERE r.totalTime < {max_time}
        RETURN r
        """
        return list(self.graph.run(query))
