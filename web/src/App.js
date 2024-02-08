import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import * as d3 from 'd3';

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredient, setSelectedIngredient] = useState('');
  const [recipes, setRecipes] = useState([]);
  const svgRef = useRef();

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

  useEffect(() => {
    if (ingredients.length === 0 || recipes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous visualization

    const simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-10))
      .force("center", d3.forceCenter(400 / 2, 500 / 2));

      const data = {
        nodes: [
          { id: selectedIngredient.id, type: 'ingredient', name: selectedIngredient.name}, // Include the selected ingredient as a node
          ...recipes.map(recipe => ({ id: recipe.id, type: 'recipe', name: recipe.name, url: recipe.url}))
        ],
        links: recipes.map(recipe => ({ source: selectedIngredient.id, target: recipe.id }))
      };
      
    // Create tooltips
    const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("display", "none");

    const link = svg.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(data.links)
      .join("line")
      .attr("stroke-width", 2);

    const node = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(data.nodes)
      .join("circle")
      .attr("r", d => d.type === 'ingredient' ? 20 : 10)
      .attr("fill", d => d.type === 'ingredient' ? 'teal' : 'orange')
      .on("mouseenter", (event, d) => {
        tooltip.transition()
          .style("display", "block");
        tooltip
          .html(`
            <div class="tooltip-title">${d.name}</div>
          `)
          .style("left", (event.pageX + 5) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on('mousemove', (event) => {
        tooltip
          .style('left', (event.pageX + 5) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on("mouseleave", () => {
        tooltip.transition()
          .style("display", "none");
      })
      .on("click", (event, d) => {
        if (d.type === 'recipe') {
          // Open the URL associated with the recipe
          window.open(d.url, "_blank");
        }})
      .call(drag(simulation));

    

    simulation
      .nodes(data.nodes)
      .on("tick", () => {
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);

        node
          .attr("cx", d => d.x)
          .attr("cy", d => d.y);
      });

    simulation.force("link").links(data.links);

     // Add zoom behavior
     svg.call(d3.zoom()
     .scaleExtent([0.1, 10])
     .on("zoom",(event) => {
      svg.selectAll('g').attr('transform', event.transform);
     })
   );

    return () => {
      simulation.stop();
    };
  }, [ingredients, recipes, selectedIngredient]);

  const handleIngredientChange = (event, ingredientName) => {
    const selectedIngredientId = event.target.value;
    setSelectedIngredient({ id: selectedIngredientId, name: ingredientName });
    // Fetch recipes based on the selected ingredient's ID
    axios.get(`http://localhost:5000/ingredients/${selectedIngredientId}/recipes`)
      .then(response => {
        setRecipes(response.data);
      })
      .catch(error => {
        console.error('Error fetching recipes:', error);
      });
  };  

  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
  }

  return (
    <div>
      <h1>Find Recipes by Ingredient</h1>
      <label htmlFor="ingredients">Select an Ingredient:</label>
      <select id="ingredients" value={selectedIngredient.id} onChange={(event) => handleIngredientChange(event, event.target.selectedOptions[0].text)}>
  <option value="">Select an ingredient</option>
  {ingredients.map(ingredient => (
    <option key={ingredient.id} value={ingredient.id}>{ingredient.name}</option>
  ))}
</select>

      <svg ref={svgRef} width="900" height="500"></svg>
    </div>
  );
}

export default App;
