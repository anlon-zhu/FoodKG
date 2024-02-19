import hashlib
import os
import ast
import re
import sys
from dotenv import load_dotenv
from functools import wraps

from flask import Flask, g, request, send_from_directory, abort, request_started
from flask_cors import CORS
from flask_restful import Resource
from flask_restful_swagger_2 import Api, Schema
from flask_json import FlaskJSON, json_response

from neo4j import GraphDatabase, basic_auth

import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)
FlaskJSON(app)

api = Api(app, title='Food Knowledge Graph', api_version='0.0.10')

########## SETUP ##########


@api.representation('application/json')
def output_json(data, code, headers=None):
    return json_response(data_=data, headers_=headers, status_=code)


def env(key, default=None, required=True):
    """
    Retrieves environment variables and returns Python natives.
    """
    try:
        value = os.environ[key]
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value
    except KeyError:
        if default or not required:
            return default
        raise RuntimeError(
            "Missing required environment variable '%s'" % key)


NEO4J_URI = env('NEO4J_URI')
NEO4J_USER = env('NEO4J_USER')
NEO4J_PASSWORD = env('NEO4J_PASSWORD')

driver = GraphDatabase.driver(
    NEO4J_URI, auth=basic_auth(NEO4J_USER, str(NEO4J_PASSWORD)))

app.config['SECRET_KEY'] = env('SECRET_KEY')


def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()


def set_user(sender, **extra):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        g.user = {'id': None}
        return
    match = re.match(r'^Token (\S+)', auth_header)
    if not match:
        abort(401, 'invalid authorization format. Follow `Token <token>`')
        return
    token = match.group(1)

    def get_user_by_token(tx, token):
        return tx.run(
            '''
            MATCH (user:User {api_key: $api_key}) RETURN user
            ''', {'api_key': token}
        ).single()

    db = get_db()
    result = db.read_transaction(get_user_by_token, token)
    try:
        g.user = result['user']
    except (KeyError, TypeError):
        abort(401, 'invalid authorization key')
    return


request_started.connect(set_user, app)


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {'message': 'no authorization provided'}, 401
        return f(*args, **kwargs)
    return wrapped

########## MODELS ##########


class IngredientModel(Schema):
    type = 'object'
    properties = {
        'name': {
            'type': 'string'
        },
        'category': {
            'type': 'string'
        }
    }
    required = ['name', 'category']


class RecipeModel(Schema):
    type = 'object'
    properties = {
        'name': {
            'type': 'string'
        },
        'url': {
            'type': 'string'
        },
        'totalTime': {
            'type': 'string'
        }
    }
    required = ['name', 'url', 'totalTime']

########## JSON SERIALIZATION ##########


def serializeIngredient(ingredient):
    return {
        'id': ingredient['id'],
        'name': ingredient['name'],
        'category': ingredient['category'],
    }


def serializeRecipe(recipe):
    return {
        'id': recipe['id'],
        'name': recipe['name'],
        'url': recipe['url'],
        'totalTime': recipe['totalTime']
    }


def hash_password(username, password):
    if sys.version[0] == 2:
        s = '{}:{}'.format(username, password)
    else:
        s = '{}:{}'.format(username, password).encode('utf-8')
    return hashlib.sha256(s).hexdigest()

########## API ##########


class ApiDocs(Resource):
    def get(self, path=None):
        if not path:
            path = 'index.html'
        return send_from_directory('swaggerui', path)


class IngredientList(Resource):
    def get(self):
        db = get_db()
        results = db.read_transaction(lambda tx: list(tx.run(
            'MATCH (i:Ingredient) RETURN ID(i) as id, i.name as name, i.category as category')))
        return [serializeIngredient(record) for record in results]


class Ingredient(Resource):
    def get(self, id):
        db = get_db()
        result = db.read_transaction(
            lambda tx: tx.run(
                'MATCH (i:Ingredient) WHERE id(i) = $id RETURN ID(i) as id, i.name as name, i.category as category',
                id=id).single())
        if result:
            return serializeIngredient(result)
        return {'message': 'Ingredient not found'}, 404


class IngredientListByRecipe(Resource):
    def get(self, id):
        db = get_db()
        results = db.read_transaction(
            lambda tx: tx.run(
                '''
                MATCH c=(r:Recipe)-[rel:CONTAINS]->(i:Ingredient)
                WHERE ID(r) = $id
                RETURN c, rel.quantity AS quantity, rel.measure AS measure
                ''', id=id).data())

        if not results:
            return {'message': 'Recipe not found'}, 404

        recipe = results[0]['c'][0]['name']
        ingredient_list = []

        if results:
            for item in results:
                c_array = item['c']
                quantity = item['quantity']
                measure = item['measure']

                # Extract node and relationship information
                if c_array[0]['name'] != recipe:
                    return {'message': 'Multiple recipes found'}, 500
                relationship = {}
                relationship['quantity'] = quantity
                relationship['measure'] = measure if measure != '<unit>' else ''
                ingredient = c_array[2]

                link = {'ingredient': ingredient,
                        'relationship': relationship}

                # Add nodes to nodeItemMap if not already present
                ingredient_list.append(link)

        return {
            'ingredient_list': ingredient_list
        }


class RecipeList(Resource):
    def get(self):
        db = get_db()
        results = db.read_transaction(lambda tx: list(tx.run(
            'MATCH (r:Recipe) RETURN ID(r) as id, r.name as name, r.url as url, r.totalTime as totalTime')))
        return [serializeRecipe(record) for record in results]


class Recipe(Resource):
    def get(self, id):
        db = get_db()
        result = db.read_transaction(
            lambda tx: tx.run(
                'MATCH (r:Recipe) WHERE id(r) = $id RETURN ID(r) as id, r.name as name, r.url as url, r.totalTime as totalTime',
                id=id).single())
        if result:
            return serializeRecipe(result)
        return {'message': 'Recipe not found'}, 404


class RecipeListByIngredient(Resource):
    def get(self, id):
        db = get_db()
        results = db.read_transaction(
            lambda tx: list(tx.run(
                '''
                MATCH (i:Ingredient)<-[:CONTAINS]-(r:Recipe)
                WHERE id(i) = $id
                RETURN ID(r) as id, r.name as name, r.url as url, r.totalTime as totalTime
                ''', id=id)))
        if results:
            return [serializeRecipe(record) for record in results]
        return {'message': 'Ingredient not found'}, 404


class RecipesByMultipleIngredients(Resource):
    def post(self):
        ingredient_ids = request.json.get('ingredientIds')

        if not ingredient_ids:
            return {'message': 'No ingredient IDs provided'}, 400

        db = get_db()

        query = """
        MATCH p=(ingredient:Ingredient)-[:PART_OF]->(recipe:Recipe)
        WHERE ID(ingredient) in $ingredientIds
        RETURN ID(recipe), p
        """
        result = db.read_transaction(lambda tx: tx.run(
            query, ingredientIds=ingredient_ids).data())

        node_item_map = {}
        link_item_map = {}
        top_recipes_map = {}

        # return the top recipes
        for item in result:
            id = item['ID(recipe)']
            p_array = item['p']

            # Extract node and relationship information
            ingredient = p_array[0]
            relationship_type = p_array[1]
            recipe = p_array[2]

            # Add nodes to nodeItemMap if not already present
            if ingredient['name'] not in node_item_map:
                ingredient['type'] = 'ingredient'
                node_item_map[ingredient['name']] = ingredient
            if recipe['name'] not in node_item_map:
                recipe['type'] = 'recipe'
                recipe['id'] = id
                node_item_map[recipe['name']] = recipe

            # Add relationship to linkItemMap and topRecipesMap
            top_recipes_map[recipe['name']] = top_recipes_map.get(
                recipe['name'], 0) + 1

            link_id = f"{ingredient['name']}_{relationship_type}_{recipe['name']}"
            link_item_map[link_id] = {
                'source': ingredient['name'],
                'target': recipe['name'],
                'relationship': relationship_type
            }

        return {
            'nodes': list(node_item_map.values()),
            'links': list(link_item_map.values()),
            'topRecipes': sorted(top_recipes_map.items(), key=lambda x: x[1], reverse=True)[:10]
        }


########## LINKING ##########
api.add_resource(IngredientList, '/ingredients')
api.add_resource(Ingredient, '/ingredients/<int:id>')
api.add_resource(IngredientListByRecipe,
                 '/recipes/<int:id>/ingredients')
api.add_resource(RecipeList, '/recipes')
api.add_resource(Recipe, '/recipes/<int:id>')
api.add_resource(RecipeListByIngredient,
                 '/ingredients/<int:id>/recipes')
api.add_resource(RecipesByMultipleIngredients,
                 '/recipes/by-ingredients')
