// colorMapGenerator.js
import * as d3 from 'd3';

function generateColorMap(nodeData) {
  if (!nodeData) {
    return null;
  }

  const scores = nodeData.map(d => d.score);
  const minScore = d3.min([1, ...scores]);
  const maxScore = d3.max([3, ...scores]);

  const colorMap = d3.scaleSequential(d3.interpolateYlGnBu)
    .domain([minScore, maxScore]);

  return colorMap;
}

export default generateColorMap;
