import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import GraphNetwork from './network';
import IngredientSelect from './ingredientSelect';
import RecipeModal from './recipeModal';
import TopRecipes from './TopRecipes';
import generateColorMap from './colorMap';
import CircularProgress from '@mui/material/CircularProgress';
import { createTheme, ThemeProvider } from '@mui/material/styles';

const BASE_URL = process.env.REACT_APP_ENV_URL || "https://ingreedient-flask-api.onrender.com/";

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredients, setSelectedIngredients] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [recipeNode, setRecipeNode] = useState('');
  const [loading, setLoading] = useState(false);

  const theme = createTheme({
    palette: {
      primary: {
        main: '#ff9800',
      },
    },
  });

  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const response = await axios.get(BASE_URL + 'ingredients');
        setIngredients(response.data);
      } catch (error) {
        console.error('Error fetching ingredients:', error);
      }
    };

    fetchIngredients();
  }, []);

  const handleIngredientChange = useCallback(async (event, newValue) => {
    setSelectedIngredients(newValue);
    setLoading(true);

    try {
      if (newValue.length === 0) {
        setGraphData(null);
      } else {
        const response = await axios.post(BASE_URL + 'recipes/by-ingredients', {
          ingredientIds: newValue.map(ingredient => ingredient.id)
        });

        // Parse the string into an object
        const recipeNodes = JSON.parse(response.data.recipeNodes);
        const ingredientNodes = JSON.parse(response.data.ingredientNodes);
        const links = response.data.links;
        const topRecipes = response.data.topRecipes;

        const data = {recipeNodes, ingredientNodes, links, topRecipes};
        setGraphData(data);
      }
    } catch (error) {
      console.error('Error fetching graph data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const colorMap = generateColorMap();

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handleMouseClick = (recipeNode) => {
    d3.select("#tooltip").style("display", "none");
    let recipeId = recipeNode.id
    setLoading(true);

    axios.get(BASE_URL + 'recipes/' + recipeId + '/ingredients')
    .then(response => {
      recipeNode.ingredients = response.data['ingredient_list'];
      setRecipeNode(recipeNode);
      setLoading(false);
      setModalOpen(true);
    })
    .catch(error => {
      console.error('Error fetching ingredient data:', error);
      setLoading(false);
    });
  };

  const handleMouseEnter = (recipeName) => {
    // Highlight logic
    const circle = d3.select(`circle[data-name="${recipeName.replace(/['"]+/g,'')}"]`);
    const node = d3.select(`g.node[data-name="${recipeName.replace(/['"]+/g,'')}"]`);
    const recipeRadius = 8;

    if (!circle.empty()) {
      circle.transition()
        .duration(300)
        .attr("r", recipeRadius * 1.5)
        .style("opacity", 0.7)
        .style("fill", "#73d6e6");

      node.append("text")
        .attr("class", "plus-sign")
        .attr("x", 0)
        .attr("y", 5)
        .attr("text-anchor", "middle")
        .attr("font-size", "16px")
        .text("+")
        .on("click", (event, d) => {
          console.log(d)
          handleMouseClick(d)
        });
    }
  };

  const handleMouseLeave = (recipeName) => {
    // Un-highlight logic
    const recipeRadius = 8;
    const circle = d3.select(`circle[data-name="${recipeName.replace(/['"]+/g,'')}"]`);

    d3.select("#tooltip").style("display", "none");
    circle
      .transition()
      .duration(200)
      .attr("r", recipeRadius)
      .style("opacity", 1)
      .style("fill", d => colorMap(d.score));
    d3.selectAll(".plus-sign").remove();
  };

  useEffect(() => {
    const svg = d3.select("#chart");
    svg.call(GraphNetwork, {
      data: graphData,
      colorMap: colorMap,
      handleMouseEnter,
      handleMouseLeave,
    });
  }, [colorMap, graphData]);

  return (
    <ThemeProvider theme={theme}>
      <div>
        <h1>in<span style={{ color: 'orange' }}>greedi</span>ent</h1>
        <div style={{ padding: '0px 20px 0px 20px' }}>
          <IngredientSelect
            ingredients={ingredients}
            selectedIngredients={selectedIngredients}
            handleIngredientChange={handleIngredientChange}
          />
        </div>
        <div style={{ position: 'relative' }}>
          <svg id='chart' width={window.innerWidth} height={window.innerHeight - 100} />
          {loading && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: 'rgba(255, 255, 255, 0.7)',
                zIndex: 9999,
              }}
            >
              <CircularProgress />
            </div>
          )}
        </div>
        {graphData && (
          <TopRecipes
            graphData={graphData}
            handleMouseEnter={handleMouseEnter}
            handleMouseLeave={handleMouseLeave}
            handleMouseClick={handleMouseClick}
          />
        )}
        <RecipeModal
          open={modalOpen}
          handleClose={handleCloseModal}
          recipeNode={recipeNode}
        />
      </div>
    </ThemeProvider>
  );
}

export default App;
