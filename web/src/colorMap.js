// colorMapGenerator.js
import * as d3 from 'd3';

function generateColorMap() {
  const colorMap = d3.scaleSequential(d3.interpolateYlOrRd)
    .domain([1, 5]);

  return colorMap;
}

export default generateColorMap;
