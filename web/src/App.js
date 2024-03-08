import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
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
  const cancelTokenSourceRef = useRef(null); // Ref to store the cancel token source

  // Define custom theme
  const theme = createTheme({
    palette: {
        primary: {
            main: '#ff9800', // Change the main color to your desired color
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
            // Retry the request after a delay
            setTimeout(fetchIngredients, 3000); // Retry after 3 seconds
        }
    };

    // Initial call to fetch ingredients
    fetchIngredients();
  }, []);

  const handleIngredientChange = (event, newValue) => {
    // Cancel the previous request before making a new one
    if (cancelTokenSourceRef.current) {
      cancelTokenSourceRef.current.cancel('Request canceled by the user');
    }

    const cancelTokenSource = axios.CancelToken.source();
    cancelTokenSourceRef.current = cancelTokenSource;

    setSelectedIngredients(newValue);
    setLoading(true);

    if (newValue.length === 0) {
      setGraphData(null);
      setLoading(false);
      return;
    }

    axios.post(BASE_URL + 'recipes/by-ingredients', { ingredientIds: newValue.map(ingredient => ingredient.id) }, { cancelToken: cancelTokenSource.token })
      .then(response => {
        // Parse the string into an object
        const recipeNodes = JSON.parse(response.data.recipeNodes);
        const ingredientNodes = JSON.parse(response.data.ingredientNodes);
        const links = response.data.links;
        const topRecipes = response.data.topRecipes;

        // Set the graph data with just the values
        setGraphData({ recipeNodes, ingredientNodes, links, topRecipes });
        setLoading(false);
      })
      .catch(error => {
        if (!axios.isCancel(error)) {
          // Ignore canceled requests
          console.error('Error fetching graph data:', error);
          setLoading(false);
        }
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

  // Memoize the color map generation function
  const colorMap = useMemo(() => {
    return generateColorMap(Object.values(graphData?.recipeNodes || {}));
  }, [graphData]);

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
      svg.call(GraphNetwork, {
        data: graphData,
        handleMouseEnter,
        handleMouseLeave,
        colorMap,
      });
  }, [svg, graphData, handleMouseEnter, handleMouseLeave, colorMap]);

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
      <svg id='chart' width={canvasWidth} height={canvasHeight}/>
      {loading && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: canvasWidth,
            height: canvasHeight,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.7)',
            zIndex: 9999, // ensure the overlay appears on top
          }}
        >
          <CircularProgress/>
        </div>
      )}
    </div>
       {graphData && <TopRecipes graphData={graphData} handleMouseEnter={handleMouseEnter} handleMouseLeave={handleMouseLeave} handleMouseClick={handleMouseClick}/>}

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
