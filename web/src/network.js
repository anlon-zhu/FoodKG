import * as d3 from "d3";

export const graphNetwork = (parent, props) => {
    const {
        data,
    } = props;

    let width = +parent.attr('width');
    let height = +parent.attr('height');
    const tooltipPadding = 15;

    // Define zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", zoomed);

    parent.call(zoom);

    let container = parent.selectAll(".container").data([null]);
    container = container.enter().append("g").attr("class", "container").merge(container);

    // Set up parent container
    let links = container.selectAll(".links").data([data.links]);
    let nodes = container.selectAll(".nodes").data([data.nodes]);

    // Enter selection
    links = links.enter().append("g").attr("class", "links").merge(links);
    nodes = nodes.enter().append("g").attr("class", "nodes").merge(nodes);

    // Define the simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).distance(25).strength(0.1).id(d => d.name))
        .force('chargeForce', d3.forceManyBody().strength(-10))
        .force("center", d3.forceCenter(width / 2, height / 2));

    // Draw links
    const link = links.selectAll("line")
        .data(data.links, d => `${d.source.name}-${d.target.name}`);

    link.exit().remove(); // Remove links that are not needed anymore

    const newLink = link.enter().append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", 0.2)
        .merge(link);

    // Draw nodes
    const node = nodes.selectAll("g.node")
        .data(data.nodes, d => d.name);

    node.exit().remove(); // Remove nodes that are not needed anymore

    const newNode = node.enter().append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .merge(node);

    // Append circles to represent nodes
    newNode.append("circle")
        .attr("r", d => d.type === 'ingredient' ? 25 : 7)
        .attr("fill", d => d.type === 'ingredient' ? '#FFA177FF' : '#F5C7B8FF')
        .merge(node)
        ;

    // Append text labels to ingredient nodes
    const text = newNode.filter(d => d.type === 'ingredient')
        .append("text")
        .attr("text-anchor", "middle")
        .text(d => d.name)
        .merge(node);

    text.each(function(d) {
            const text = d3.select(this);
            const circleRadius = d.type === 'ingredient' ? 25 : 7;
            const availableWidth = circleRadius * 2; // Double the circle radius to account for diameter
            const availableHeight = circleRadius * 2; // Double the circle radius to account for diameter
            const textWidth = this.getBBox().width;
            const textHeight = this.getBBox().height;
        
            // Calculate the scale factor for font size
            const scaleFactor = Math.min(availableWidth / textWidth, availableHeight / textHeight);
        
            // Apply the scale factor to adjust font size
            const fontSize = Math.floor(12 * scaleFactor); // Adjust the base font size as needed
            text.style("font-size", `${fontSize}px`);
    });
    

    // Define the tick function
    simulation.on("tick", ticked);
    simulation.force("link").links(data.links);

    // Tooltip
    newNode.on("mouseenter", (event, d) => {
        d3.select("#tooltip")
        .style("display", "block")
        .html(`<div class="tooltip-title">${d.name}</div>`)
        .style("left", (event.pageX + tooltipPadding) + "px")
        .style("top", (event.pageY - tooltipPadding) + "px");
    })
    .on("mousemove", (event) => {
        d3.select("#tooltip")
        .style("left", (event.pageX + tooltipPadding) + "px")
        .style("top", (event.pageY - tooltipPadding) + "px");
    })
    .on("mouseleave", () => {
        d3.select("#tooltip")
        .style("display", "none");
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
        if (!event.active) simulation.alphaTarget(0.4).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0.1);
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
