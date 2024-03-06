import { useState, useEffect } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import GraphNetwork from './network';
import IngredientSelect from './ingredientSelect';
import RecipeModal from './recipeModal';
import TopRecipes from './TopRecipes';

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
          // Parse the string into an object
        const recipeNodes = JSON.parse(response.data.recipeNodes);
        const ingredientNodes = JSON.parse(response.data.ingredientNodes);
        const links = response.data.links;
        const topRecipes = response.data.topRecipes;

        // Set the graph data with just the values
        setGraphData({ recipeNodes, ingredientNodes, links, topRecipes });
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
       {graphData && <TopRecipes graphData={graphData} />}

      <RecipeModal
        open={modalOpen}
        handleClose={handleCloseModal}
        recipeNode={recipeNode}
      />
    </div>
  );
}

export default App;
