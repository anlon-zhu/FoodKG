import React, { useState, useEffect } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import { graphNetwork } from './network';
import IngredientSelect from './ingredientSelect'; // Import the component

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredients, setSelectedIngredients] = useState([]);

  useEffect(() => {
    // Fetch ingredients list from your Flask API
    axios.get('http://localhost:5000/ingredients')
      .then(response => {
        setIngredients(response.data);
      })
      .catch(error => {
        console.error('Error fetching ingredients:', error);
      });
  }, []);

  const handleIngredientChange = (event, newValue) => {
    setSelectedIngredients(newValue);
    
    // Check if newValue is empty
    if (newValue.length === 0) {
      // Clear the graph or perform any other necessary action
      updateGraph(null);
      return;
    }
    
    // Fetch graph data based on selected ingredient
    axios.post('http://localhost:5000/recipes/by-ingredients', { ingredientIds: newValue.map(ingredient => ingredient.id)})
      .then(response => {
        updateGraph(response.data);
      })
      .catch(error => {
        console.error('Error fetching graph data:', error);
      });
  };

  const svg = d3.select("#chart");
    const canvasWidth = window.innerWidth;
    const canvasHeight = window.innerHeight;

  const updateGraph = (data) => {
    svg.call (graphNetwork, {
        data: data,
      });
    }

  return (
    <div>
      <h1>flavornet</h1>
      <IngredientSelect
        ingredients={ingredients}
        selectedIngredients={selectedIngredients}
        handleIngredientChange={handleIngredientChange}
      />
      <div>
        <svg id='chart' width={canvasWidth} height={canvasHeight- 100}/>
      </div>
    </div>
  );
}

export default App;
