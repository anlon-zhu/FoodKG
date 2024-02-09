import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import * as d3 from 'd3';

function App() {
  const [ingredients, setIngredients] = useState([]);
  const [selectedIngredients, setSelectedIngredients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const svgRef = useRef();

  useEffect(() => {
    axios.get('http://localhost:5000/ingredients')
      .then(response => {
        setIngredients(response.data);
      })
      .catch(error => {
        console.error('Error fetching ingredients:', error);
      });
  }, []);

  useEffect(() => {
    if (selectedIngredients.length === 0) return;

    // Fetch recipes for all selected ingredients
    Promise.all(selectedIngredients.map(ingredient =>
      axios.get(`http://localhost:5000/ingredients/${ingredient.id}/recipes`)
    )).then(responses => {
      // Flatten recipes and remove duplicates
      const newRecipes = responses.flatMap(response => response.data).reduce((acc, current) => {
        const x = acc.find(item => item.id === current.id);
        if (!x) {
          return acc.concat([current]);
        } else {
          return acc;
        }
      }, []);
      setRecipes(newRecipes);
    }).catch(error => console.error('Error fetching recipes:', error));

  }, [selectedIngredients]);

  useEffect(() => {
    if (selectedIngredients.length === 0 || recipes.length === 0) return;
  
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous visualization
  
    const simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-50))
      .force("center", d3.forceCenter(900 / 2, 500 / 2));
  
    const ingredientNodes = selectedIngredients.map(ingredient => ({
      ...ingredient,
      type: 'ingredient'
    }));
  
    const recipeNodes = recipes.map(recipe => ({
      ...recipe,
      type: 'recipe'
    }));
  
    const links = recipes.flatMap(recipe =>
      selectedIngredients.map(ingredient => ({
        source: ingredient.id,
        target: recipe.id
      }))
    );
  
    const data = {
      nodes: [...ingredientNodes, ...recipeNodes],
      links: links
    };
  
    // Continue with the visualization logic (nodes, links, tooltips, drag behavior, etc.)
    // This includes creating link and node elements, handling drag events, and adding tooltips
    // You may use the existing code as a reference, making sure to replace any specific logic
    // with the updated data structure and visualization requirements
  
    // Create link SVG elements
  const link = svg.append("g")
  .attr("stroke", "#999")
  .attr("stroke-opacity", 0.6)
  .selectAll("line")
  .data(data.links)
  .join("line")
  .attr("stroke-width", d => Math.sqrt(d.value));

// Create node SVG elements
const node = svg.append("g")
  .attr("stroke", "#fff")
  .attr("stroke-width", 1.5)
  .selectAll("circle")
  .data(data.nodes)
  .join("circle")
  .attr("r", 10)
  .attr("fill", d => d.type === 'ingredient' ? 'teal' : 'orange')
  .call(drag(simulation));

// Create tooltips
node.on("mouseenter", (event, d) => {
  d3.select("#tooltip")
    .style("display", "block")
    .html(`<div class="tooltip-title">${d.name}</div>`)
    .style("left", (event.pageX + 5) + "px")
    .style("top", (event.pageY - 28) + "px");
})
.on("mousemove", (event) => {
  d3.select("#tooltip")
    .style("left", (event.pageX + 5) + "px")
    .style("top", (event.pageY - 28) + "px");
})
.on("mouseleave", () => {
  d3.select("#tooltip")
    .style("display", "none");
});
    simulation
      .nodes(data.nodes)
      .on("tick", ticked);
  
    simulation.force("link")
      .links(data.links);
  
    function ticked() {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
  
      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    }
  
    // Make sure to implement the drag behavior and zoom functionality as before
    // This ensures interactivity within your visualization
  
  }, [selectedIngredients, recipes]);
  

  // Update handleIngredientChange to support multiple selections
  const handleIngredientChange = event => {
    const selectedOptions = Array.from(event.target.selectedOptions).map(option => ({
      id: option.value,
      name: option.text
    }));
    setSelectedIngredients(selectedOptions);
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
  // Update the rest of your component to handle multiple ingredients
  // Specifically, the visualization logic inside useEffect that uses `ingredients`, `recipes`, and `selectedIngredient`
  // Note: Ensure to update your visualization logic to handle multiple ingredients and their connected recipes


  return (
    <div>
      <h1>Find Recipes by Ingredient</h1>
      <label htmlFor="ingredients">Select an Ingredient:</label>
      <select id="ingredients" value={selectedIngredients.map(si => si.id)} onChange={handleIngredientChange} multiple>
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
