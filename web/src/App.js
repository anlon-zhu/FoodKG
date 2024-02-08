import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredient, setSelectedIngredient] = useState('');
  const [recipes, setRecipes] = useState([]);

  useEffect(() => {
    // Fetch list of ingredients from Flask API
    axios.get('http://localhost:5000/ingredients')
      .then(response => {
        setIngredients(response.data);
      })
      .catch(error => {
        console.error('Error fetching ingredients:', error);
      });
  }, []);

  const handleIngredientChange = (event) => {
    const selectedIngredientId = event.target.value;
    setSelectedIngredient(selectedIngredientId);
    // Fetch recipes based on the selected ingredient's ID
    axios.get(`http://localhost:5000/ingredients/${selectedIngredientId}/recipes`)
      .then(response => {
        setRecipes(response.data);
      })
      .catch(error => {
        console.error('Error fetching recipes:', error);
      });
  };

  return (
    <div>
      <h1>Find Recipes by Ingredient</h1>
      <label htmlFor="ingredients">Select an Ingredient:</label>
      <select id="ingredients" value={selectedIngredient} onChange={handleIngredientChange}>
        <option value="">Select an ingredient</option>
        {ingredients.map(ingredient => (
          <option key={ingredient.id} value={ingredient.id}>{ingredient.name}</option>
        ))}
      </select>

      {recipes.length > 0 && (
        <div>
          <h2>Recipes with {selectedIngredient}:</h2>
          <ul>
            {recipes.map(recipe => (
              <li key={recipe.id}>{recipe.name}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
