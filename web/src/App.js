import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import GraphNetwork from './network';
import IngredientSelect from './ingredientSelect';
import RecipeModal from './recipeModal';
import TopRecipes from './TopRecipes';
import generateColorMap from './colorMap';

const BASE_URL = process.env.REACT_APP_ENV_URL || "https://ingreedient-flask-api.onrender.com/";
console.log(BASE_URL)

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredients, setSelectedIngredients] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [recipeNode, setRecipeNode] = useState('');

  useEffect(() => {
    // Fetch ingredients list from your Flask API
    axios.get(BASE_URL + 'ingredients')
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
    
    axios.post(BASE_URL + 'recipes/by-ingredients', { ingredientIds: newValue.map(ingredient => ingredient.id)})
      .then(response => {
          // Parse the string into an object
        console.log(response)
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

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handleMouseClick = useCallback((recipeNode) => {
    d3.select("#tooltip").style("display", "none");
    let recipeId = recipeNode.id;
    axios.get(BASE_URL + 'recipes/' + recipeId + '/ingredients')
      .then(response => {
        recipeNode.ingredients = response.data['ingredient_list'];
        setRecipeNode(recipeNode);
        setModalOpen(true);
      })
      .catch(error => {
        console.error('Error fetching ingredient data:', error);
      });
  }, []);

  const handleMouseEnter =  useCallback((recipeName) => {
      // Trigger hover event in sync between the graph and the list
      const circle = d3.select(`circle[data-name="${recipeName}"]`);
      const node = d3.select(`g.node[data-name="${recipeName}"]`);
      const recipeRadius = 8;

      if (!circle.empty()) {
          circle.transition()
              .duration(300)
              .attr("r", recipeRadius * 1.5)
              .style("opacity", 0.7)
              .style("fill", "#ff9800");
          
          // Append a plus sign
          node.append("text")
              .attr("class", "plus-sign")
              .attr("x", 0)
              .attr("y", 5)
              .attr("text-anchor", "middle")
              .attr("font-size", "16px")
              .text("+")
              .on("click", (event, d) => {
                handleMouseClick(d)
              });
      }
  }, [handleMouseClick]);

  const colorMap = generateColorMap(Object.values(graphData?.recipeNodes || {}));

  const handleMouseLeave = useCallback((recipeName) => { 
      const recipeRadius = 8;
      const circle = d3.select(`circle[data-name="${recipeName}"]`);

      d3.select("#tooltip").style("display", "none");
      circle
          .transition()
          .duration(200)
          .attr("r", recipeRadius)
          .style("opacity", 1)
          .style("fill", d => colorMap(d.score));
      d3.selectAll(".plus-sign").remove();
  }, [colorMap]);

  useEffect(() => {
    if (graphData) {
      // You can set up D3 simulation here if needed
      svg.selectAll("*").remove(); // Clear previous content

      // Call the GraphNetwork component with props
      svg.call(GraphNetwork, {
        data: graphData,
        modalOpen,
        recipeNode,
        handleMouseEnter,
        handleMouseLeave
      });
    } else {
      svg.selectAll("*").remove(); // Clear the SVG if there's no data
    }
  }, [svg, graphData, modalOpen, recipeNode, handleMouseEnter, handleMouseLeave]);

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
        <svg id='chart' width={canvasWidth} height={canvasHeight}/>
      </div>
       {graphData && <TopRecipes graphData={graphData} handleMouseEnter={handleMouseEnter} handleMouseLeave={handleMouseLeave} handleMouseClick={handleMouseClick}/>}

      <RecipeModal
        open={modalOpen}
        handleClose={handleCloseModal}
        recipeNode={recipeNode}
      />
    </div>
  );
}

export default App;
