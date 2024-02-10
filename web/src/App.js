import { useState, useEffect } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import GraphNetwork from './network';
import IngredientSelect from './ingredientSelect'; // Import the component
import RecipeModal from './recipeModal';

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredients, setSelectedIngredients] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [recipeNode, setRecipeNode] = useState('');

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
    
    if (newValue.length === 0) {
      setGraphData(null);
      return;
    }
    
    axios.post('http://localhost:5000/recipes/by-ingredients', { ingredientIds: newValue.map(ingredient => ingredient.id)})
      .then(response => {
        setGraphData(response.data);
      })
      .catch(error => {
        console.error('Error fetching graph data:', error);
      });
  };

  const svg = d3.select("#chart");
  const canvasWidth = window.innerWidth;
  const canvasHeight = window.innerHeight - 100;

  useEffect(() => {
    if (graphData) {
      // You can set up D3 simulation here if needed
      svg.selectAll("*").remove(); // Clear previous content

      // Call the GraphNetwork component with props
      svg.call(GraphNetwork, {
        data: graphData,
        modalOpen,
        recipeNode,
        handleOpenModal,
        handleCloseModal
      });
    } else {
      svg.selectAll("*").remove(); // Clear the SVG if there's no data
    }
  }, [svg, graphData, modalOpen, recipeNode]);

  const handleOpenModal = (recipeNode) => {
    let recipeId = recipeNode.id;
    axios.get('http://localhost:5000/recipes/' + recipeId + '/ingredients')
      .then(response => {
        console.log('Recipe ingredients:', response.data['ingredient_list'])
        recipeNode.ingredients = response.data['ingredient_list'];
        setRecipeNode(recipeNode);
        setModalOpen(true);
      })
      .catch(error => {
        console.error('Error fetching ingredient data:', error);
      });
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };
  
  return (
    <div>
      <h1>in<span style={{ color: 'orange' }}>greedi</span>ent</h1>
      <div style={{ padding: '0px 20px 0px 20px' }}>
      <IngredientSelect
        ingredients={ingredients}
        selectedIngredients={selectedIngredients}
        handleIngredientChange={handleIngredientChange}
      />
      </div>
      <div>
        <svg id='chart' width={canvasWidth} height={canvasHeight- 100}/>
      </div>
      <RecipeModal
        open={modalOpen}
        handleClose={handleCloseModal}
        recipeNode={recipeNode}
      />
    </div>
  );
}

export default App;
