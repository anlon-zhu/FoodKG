import * as d3 from "d3";
import generateColorMap from './colorMap';

function GraphNetwork (parent, props) {
    const {
        data,
        handleOpenModal,
    } = props;

    if (!data) {
        parent.selectAll("*").remove();
        return;
    }

    // Constants 
    let recipeNodeData = Object.values(data.recipeNodes)
    let ingredientNodeData = Object.values(data.ingredientNodes)
    let nodedata = [...recipeNodeData, ...ingredientNodeData]
    let linkdata = data.links
    let recipeRadius = 8;
    let ingredientRadius = 25;
    let width = +parent.attr('width');
    let height = +parent.attr('height');
    const tooltipPadding = 15;
    // Set up color map
    const colorMap = generateColorMap(nodedata);

    // Set up parent container
    let container = parent.selectAll(".container").data([null]);
    container = container.enter().append("g").attr("class", "container").merge(container);
    let links = container.selectAll(".links").data([linkdata]);
    let nodes = container.selectAll(".nodes").data([nodedata]);
    links = links.enter().append("g").attr("class", "links").merge(links);
    nodes = nodes.enter().append("g").attr("class", "nodes").merge(nodes);

    // Define the simulation
    const simulation = d3.forceSimulation(nodedata)
        .force("link", d3.forceLink(data.links).distance(30).strength(0.1).id(d => d.name))
        .force('chargeForce', d3.forceManyBody().strength(-20))
        .force("center", d3.forceCenter(width / 2, height / 2));
    
    // Define zoom behavior
    const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", zoomed);

    parent.call(zoom);

    // Add a legend with the gradient colormap to the parent
    const defs = parent.append("defs");
    const linearGradient = defs.append("linearGradient")
        .attr("id", "linear-gradient");
    linearGradient.selectAll("stop")
        .data(colorMap.ticks().map((t, i, n) => ({ offset: `${100 * i / n.length}%`, color: colorMap(t) })))
        .enter().append("stop")
        .attr("offset", d => d.offset)
        .attr("stop-color", d => d.color);
    parent.append("rect")
        .attr("x", 20)
        .attr("y", 10)
        .attr("width", 300)
        .attr("height", 20)
        .attr("rx", 10)
        .attr("ry", 10)
        .style("fill", "url(#linear-gradient)")
        .style("stroke", "rgba(0, 0, 0, 0.87)");
    parent.append("text")
        .attr("x", 20)
        .attr("y", 45)
        .attr("font-size", "12px")
        .text("Few ingredients");
    parent.append("text")
            .attr("x", 260)
            .attr("y", 45)
            .attr("font-size", "12px")
            .text("Cook this!");    

    // Draw links
    const link = links.selectAll("line")
        .data(linkdata, d => `${d.source.name}-${d.target.name}`);

    link.exit().remove(); // Remove links that are not needed anymore

    const newLink = link.enter().append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", 0.2)
        .merge(link);

    // Draw nodes
    const node = nodes.selectAll("g.node")
        .data(nodedata, d => d.name);

    node.exit().remove();

    const newNode = node.enter().append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .merge(node);
    const circles = newNode.selectAll("circle")
    .data(d => [d]);

    circles.exit().remove();
    circles.enter().append("circle") // Append circles to newNode
    .attr("class", "node-circle")
    .attr("r", d => d.type === 'ingredient' ? ingredientRadius : recipeRadius)
    .attr("fill", d => d.type === 'recipe' ? colorMap(d.score) : '#dad2bc')
    .merge(circles); // Merge enter and update selections

    // Append text labels to ingredient nodes using foreignObject for text wrapping
    const foreignText = newNode.filter(d => d.type === 'ingredient')
    .append("foreignObject")
    .attr("width", ingredientRadius * 1.5)
    .attr("height", ingredientRadius * 1.5)
    .attr("x", -(ingredientRadius * .75))
    .attr("y", -(ingredientRadius *.75 ))
    .merge(node);

    foreignText.html(d => `
        <div class="text-wrapper"><span>${d.name}</span></div>
    `);

    // Define the tick function
    simulation.on("tick", ticked);
    simulation.force("link").links(data.links);

    // Tooltip
    newNode.on("mouseenter", (event, d) => {
        const circle = d3.select(event.currentTarget).select(".node-circle");

        if (d.type === 'recipe') {
            d3.select("#tooltip")
            .style("display", "block")
            .html(`<div class="tooltip-title">${d.name}</div>`)
            .style("left", (event.pageX + tooltipPadding) + "px")
            .style("top", (event.pageY - tooltipPadding) + "px");

            circle
                .transition()
                .duration(300)
                .attr("r", recipeRadius * 1.5)
                .style("opacity", 0.7)
                .style("fill", "#ff9800");

            // Append a plus sign
            d3.select(event.currentTarget).append("text")
                .attr("class", "plus-sign")
                .attr("x", 0)
                .attr("y", 5)
                .attr("text-anchor", "middle")
                .attr("font-size", "16px")
                .text("+")
                .on("click", (event, d) => {
                    d3.select("#tooltip").style("display", "none");
                    handleOpenModal(d);
                });
        } else {
            circle
                .transition()
                .duration(300)
                .attr("r", ingredientRadius * 1.25);
        }
    })
    .on("mousemove", (event) => {
        d3.select("#tooltip")
        .style("left", (event.pageX + tooltipPadding) + "px")
        .style("top", (event.pageY - tooltipPadding) + "px");
    })
    .on("mouseleave", (event, d) => {
        const circle = d3.select(event.currentTarget).select(".node-circle");

        if (d.type === 'recipe') {
            d3.select("#tooltip")
            .style("display", "none");
    
            // Restore node size                
            circle.transition()
                .duration(200)
                .attr("r", recipeRadius)
                .style("opacity", 1)
                .style("fill", d => colorMap(d.score));
        
            // Remove the plus sign
            d3.select(event.currentTarget).select(".plus-sign").remove();
        }
        else {
            circle
                .transition()
                .duration(200)
                .attr("r", ingredientRadius);
        }
    });

    function ticked() {
        newLink
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        newNode
            .attr("transform", d => `translate(${d.x},${d.y})`);
    }

    // Drag functions
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
        if (!event.active) simulation.alphaTarget(0.2).restart();
        event.subject.fx = null;
        event.subject.fy = null;
    }

    function zoomed(event) {
        container.attr("transform", event.transform);
    }

    // Resize function
    function resize() {
        // Get the width and height of the canvas (assuming it is the parent)
        const canvas = parent.node().parentElement; // Get the parent element (canvas)
        const canvasWidth = canvas.clientWidth;
        const canvasHeight = canvas.clientHeight;
    
        // Update the width and height attributes of the SVG container
        parent.attr("width", canvasWidth).attr("height", canvasHeight);
    
        // Update the simulation's center force based on the new dimensions
        simulation.force("center", d3.forceCenter(canvasWidth / 2, canvasHeight / 2));
    }    

    // Call resize when window size changes
    d3.select(window).on("resize", resize);

    return parent;
}

export default GraphNetwork;