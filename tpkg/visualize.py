# visualize.py
import json
from collections import defaultdict

INPUT = "kg_output.json"
OUTPUT = "kg_visualizer.html"


def calculate_node_metrics(kg):
    """Calculate importance metrics for each node"""
    metrics = {}
    
    for noun, data in kg.items():
        children = data.get("children", [])
        # Calculate degree (number of connections)
        degree = len(children)
        
        # Calculate how many times this node appears in other nodes' children
        incoming = sum(1 for other_data in kg.values() 
                      if noun in other_data.get("children", []))
        
        metrics[noun] = {
            "outgoing": degree,
            "incoming": incoming,
            "total": degree + incoming
        }
    
    return metrics


def assign_hierarchy_levels(kg):
    """Assign hierarchical levels based on connectivity"""
    metrics = calculate_node_metrics(kg)
    
    # Sort by importance
    sorted_nodes = sorted(metrics.items(), 
                         key=lambda x: (x[1]['total'], x[1]['outgoing']), 
                         reverse=True)
    
    levels = {}
    assigned = set()
    
    # Top 10% are level 0 (core concepts)
    level_0_count = max(3, len(sorted_nodes) // 10)
    for noun, _ in sorted_nodes[:level_0_count]:
        levels[noun] = 0
        assigned.add(noun)
    
    # Assign levels based on distance from core
    current_level = 1
    max_iterations = len(kg)
    iteration = 0
    
    while len(assigned) < len(kg) and iteration < max_iterations:
        new_assignments = False
        for noun, data in kg.items():
            if noun in assigned:
                continue
            children = data.get("children", [])
            # If any child is in previous level, assign current level
            if any(child in assigned for child in children):
                levels[noun] = current_level
                assigned.add(noun)
                new_assignments = True
        
        if not new_assignments:
            # Assign remaining nodes to current level
            for noun in kg:
                if noun not in assigned:
                    levels[noun] = current_level
                    assigned.add(noun)
            break
        current_level += 1
        iteration += 1
    
    return levels


def build_d3_graph(kg):
    MAX_EDGES_PER_NODE = 8
    
    # Calculate metrics and hierarchy
    metrics = calculate_node_metrics(kg)
    levels = assign_hierarchy_levels(kg)
    
    nodes = []
    
    # Build nodes with full data
    for noun, data in kg.items():
        nodes.append({
            "id": noun,
            "contexts": data.get("contexts", {}),
            "children": data.get("children", []),
            "level": levels.get(noun, 0),
            "degree": metrics[noun]["total"],
            "outgoing": metrics[noun]["outgoing"],
            "incoming": metrics[noun]["incoming"]
        })
    
    links = []
    seen = set()

    for parent, data in kg.items():
        children = data.get("children", [])[:MAX_EDGES_PER_NODE]

        for child in children:
            if parent == child:
                continue
            if child not in kg:
                continue

            edge_key = tuple(sorted([parent, child]))
            if edge_key in seen:
                continue
            seen.add(edge_key)

            links.append({
                "source": parent,
                "target": child,
                "value": 1
            })

    return {"nodes": nodes, "links": links}


def generate_html(d3_data, kg):
    """
    Enhanced visualization with hierarchy and advanced features
    """

    html = f"""
<!DOCTYPE html>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  
  body {{ 
    margin: 0; 
    background: #0a0a0a; 
    font-family: 'Segoe UI', Arial, sans-serif;
    overflow: hidden;
    color: #fff;
  }}
  
  #graph-container {{
    position: relative;
    width: 100vw;
    height: 100vh;
  }}
  
  /* Control Panel */
  #control-panel {{
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(20, 20, 30, 0.95);
    border: 2px solid #4aa3ff;
    border-radius: 12px;
    padding: 20px;
    width: 320px;
    max-height: calc(100vh - 240px);
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    z-index: 100;
  }}
  
  #control-panel h3 {{
    margin: 0 0 15px 0;
    color: #4aa3ff;
    font-size: 18px;
    border-bottom: 2px solid #4aa3ff;
    padding-bottom: 8px;
  }}
  
  .control-section {{
    margin: 20px 0;
    padding: 15px;
    background: rgba(40, 40, 50, 0.5);
    border-radius: 8px;
    border-left: 3px solid #4aa3ff;
  }}
  
  .control-section h4 {{
    margin: 0 0 12px 0;
    color: #6bc5ff;
    font-size: 14px;
    font-weight: 600;
  }}
  
  .button-group {{
    display: flex;
    gap: 10px;
    margin: 10px 0;
  }}
  
  button {{
    background: #4aa3ff;
    border: none;
    color: white;
    padding: 10px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s;
    flex: 1;
  }}
  
  button:hover {{
    background: #6bc5ff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 163, 255, 0.4);
  }}
  
  button.active {{
    background: #ff6b6b;
  }}
  
  button.secondary {{
    background: #666;
  }}
  
  button.secondary:hover {{
    background: #888;
  }}
  
  input[type="text"] {{
    width: 100%;
    padding: 10px;
    border: 2px solid #4aa3ff;
    border-radius: 6px;
    background: rgba(20, 20, 30, 0.8);
    color: white;
    font-size: 14px;
    margin: 8px 0;
  }}
  
  input[type="text"]:focus {{
    outline: none;
    border-color: #6bc5ff;
    box-shadow: 0 0 0 3px rgba(74, 163, 255, 0.2);
  }}
  
  input[type="range"] {{
    width: 100%;
    margin: 10px 0;
  }}
  
  .slider-label {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #aaa;
    margin-bottom: 5px;
  }}
  
  /* Info Panel */
  #info-panel {{
    position: absolute;
    top: 20px;
    right: 20px;
    width: 380px;
    max-height: 90vh;
    background: rgba(20, 20, 30, 0.95);
    border: 2px solid #4aa3ff;
    border-radius: 12px;
    padding: 25px;
    overflow-y: auto;
    display: none;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    z-index: 100;
  }}
  
  #info-panel h2 {{
    margin-top: 0;
    color: #4aa3ff;
    border-bottom: 2px solid #4aa3ff;
    padding-bottom: 12px;
    font-size: 24px;
  }}
  
  #info-panel h3 {{
    color: #6bc5ff;
    margin-top: 20px;
    margin-bottom: 10px;
    font-size: 15px;
    font-weight: 600;
  }}
  
  #info-panel p {{
    line-height: 1.7;
    margin: 10px 0;
    font-size: 13px;
    color: #ddd;
  }}
  
  .context-section {{
    background: rgba(40, 40, 50, 0.6);
    padding: 15px;
    margin: 12px 0;
    border-radius: 8px;
    border-left: 3px solid #4aa3ff;
  }}
  
  .metric-badge {{
    display: inline-block;
    background: #4aa3ff;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 12px;
    margin: 5px 5px 5px 0;
    font-weight: 600;
  }}
  
  .warning-badge {{
    display: inline-block;
    background: #ffa94d;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 12px;
    margin: 10px 0;
    font-weight: 600;
  }}
  
  .children-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }}
  
  .child-tag {{
    background: #6bc5ff;
    padding: 6px 14px;
    border-radius: 16px;
    font-size: 12px;
    display: inline-block;
    cursor: pointer;
    transition: all 0.3s;
  }}
  
  .child-tag:hover {{
    background: #4aa3ff;
    transform: scale(1.05);
  }}
  
  .close-btn {{
    position: absolute;
    top: 20px;
    right: 20px;
    background: #ff4444;
    border: none;
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 20px;
    line-height: 1;
    transition: all 0.3s;
  }}
  
  .close-btn:hover {{
    background: #ff6666;
    transform: rotate(90deg);
  }}
  
  /* Graph Elements */
  text {{ 
    fill: #fff; 
    font-family: 'Segoe UI', Arial; 
    font-size: 12px; 
    pointer-events: none;
    text-shadow: 2px 2px 4px #000, -1px -1px 3px #000;
    font-weight: 600;
  }}
  
  .link {{ 
    stroke: #444; 
    stroke-opacity: 0.4; 
  }}
  
  .link.highlighted {{
    stroke: #4aa3ff;
    stroke-opacity: 1;
    stroke-width: 3px;
  }}
  
  .node {{ 
    stroke: #fff; 
    stroke-width: 2px; 
    cursor: pointer;
    transition: all 0.3s;
  }}
  
  .node:hover {{
    stroke-width: 3px;
    filter: brightness(1.3);
  }}
  
  .node.highlighted {{
    stroke: #ffd93d;
    stroke-width: 4px;
    filter: drop-shadow(0 0 8px #ffd93d);
  }}
  
  .node.connected {{
    stroke: #4aa3ff;
    stroke-width: 3px;
  }}
  
  .node.dimmed {{
    opacity: 0.2;
  }}
  
  .node.isolated {{
    stroke: #ffa94d;
    stroke-width: 3px;
    stroke-dasharray: 4,2;
  }}
  
  /* Tooltip */
  .tooltip {{
    position: absolute;
    background: rgba(10, 10, 20, 0.98);
    color: #fff;
    padding: 15px;
    border-radius: 8px;
    border: 2px solid #4aa3ff;
    pointer-events: none;
    font-size: 13px;
    max-width: 320px;
    display: none;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0,0,0,0.8);
  }}
  
  .tooltip .title {{
    font-weight: bold;
    color: #4aa3ff;
    margin-bottom: 10px;
    font-size: 16px;
  }}
  
  .tooltip .metrics {{
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #444;
    font-size: 11px;
    color: #aaa;
  }}
  
  /* Legend */
  #legend {{
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(20, 20, 30, 0.95);
    border: 2px solid #4aa3ff;
    border-radius: 10px;
    padding: 15px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    max-width: 280px;
  }}
  
  #legend h4 {{
    margin: 0 0 12px 0;
    color: #4aa3ff;
    font-size: 14px;
  }}
  
  .legend-item {{
    display: flex;
    align-items: center;
    margin: 8px 0;
    font-size: 11px;
  }}
  
  .legend-circle {{
    width: 18px;
    height: 18px;
    border-radius: 50%;
    margin-right: 10px;
    border: 2px solid white;
    flex-shrink: 0;
  }}
  
  /* Stats Panel */
  #stats-panel {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    background: rgba(20, 20, 30, 0.95);
    border: 2px solid #4aa3ff;
    border-radius: 10px;
    padding: 15px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    min-width: 200px;
  }}
  
  #stats-panel h4 {{
    margin: 0 0 12px 0;
    color: #4aa3ff;
    font-size: 14px;
  }}
  
  .stat-row {{
    display: flex;
    justify-content: space-between;
    margin: 6px 0;
    font-size: 12px;
  }}
  
  .stat-label {{
    color: #aaa;
  }}
  
  .stat-value {{
    color: #4aa3ff;
    font-weight: bold;
  }}
  
  /* Scrollbar */
  ::-webkit-scrollbar {{
    width: 8px;
  }}
  
  ::-webkit-scrollbar-track {{
    background: rgba(40, 40, 50, 0.5);
    border-radius: 4px;
  }}
  
  ::-webkit-scrollbar-thumb {{
    background: #4aa3ff;
    border-radius: 4px;
  }}
  
  ::-webkit-scrollbar-thumb:hover {{
    background: #6bc5ff;
  }}
</style>
<body>

<div id="graph-container">
  <svg id="graph"></svg>
  
  <!-- Control Panel -->
  <div id="control-panel">
    <h3>🎛️ Graph Controls</h3>
    
    <div class="control-section">
      <h4>🔍 Search</h4>
      <input type="text" id="search-input" placeholder="Search for a concept...">
    </div>
    
    <div class="control-section">
      <h4>📊 Layout Mode</h4>
      <div class="button-group">
        <button id="force-layout" class="active">Force</button>
        <button id="hierarchy-layout">Hierarchy</button>
      </div>
    </div>
    
    <div class="control-section">
      <h4>🎨 View Options</h4>
      <button id="toggle-labels">Hide Labels</button>
      <button id="reset-view" class="secondary">Reset View</button>
    </div>
    
    <div class="control-section">
      <h4>🔗 Connection Filter</h4>
      <div class="slider-label">
        <span>Min Connections:</span>
        <span id="filter-value">0</span>
      </div>
      <input type="range" id="connection-filter" min="0" max="20" value="0" step="1">
    </div>
  </div>
  
  <!-- Info Panel -->
  <div id="info-panel">
    <button class="close-btn" onclick="closePanel()">×</button>
    <div id="panel-content"></div>
  </div>
  
  <!-- Legend -->
  <div id="legend">
    <h4>📍 Node Hierarchy</h4>
    <div class="legend-item">
      <div class="legend-circle" style="background: #ff6b6b;"></div>
      <span>Core Concepts (Level 0)</span>
    </div>
    <div class="legend-item">
      <div class="legend-circle" style="background: #4aa3ff;"></div>
      <span>Primary (Level 1)</span>
    </div>
    <div class="legend-item">
      <div class="legend-circle" style="background: #51cf66;"></div>
      <span>Secondary (Level 2)</span>
    </div>
    <div class="legend-item">
      <div class="legend-circle" style="background: #ffd93d;"></div>
      <span>Tertiary (Level 3+)</span>
    </div>
    <div class="legend-item">
      <div class="legend-circle" style="background: #666; border-color: #ffa94d; border-style: dashed;"></div>
      <span>Isolated (No connections)</span>
    </div>
    <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #444; font-size: 10px; color: #aaa;">
      Node size = # of connections
    </div>
  </div>
  
  <!-- Stats Panel -->
  <div id="stats-panel">
    <h4>📈 Statistics</h4>
    <div class="stat-row">
      <span class="stat-label">Total Nodes:</span>
      <span class="stat-value" id="stat-nodes">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Total Edges:</span>
      <span class="stat-value" id="stat-edges">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Visible Nodes:</span>
      <span class="stat-value" id="stat-visible">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Hierarchy Levels:</span>
      <span class="stat-value" id="stat-levels">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Isolated Nodes:</span>
      <span class="stat-value" id="stat-isolated">0</span>
    </div>
  </div>
  
  <div class="tooltip" id="tooltip"></div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>

const graph = {json.dumps(d3_data)};
const fullKG = {json.dumps(kg)};

const width = window.innerWidth;
const height = window.innerHeight;

// Color scale for hierarchy levels
const colorScale = d3.scaleOrdinal()
  .domain([0, 1, 2, 3])
  .range(['#ff6b6b', '#4aa3ff', '#51cf66', '#ffd93d']);

// Size scale based on degree
const maxDegree = d3.max(graph.nodes, d => d.degree) || 1;
const sizeScale = d3.scaleLinear()
  .domain([0, maxDegree])
  .range([8, 20]);

const svg = d3.select("#graph")
    .attr("width", width)
    .attr("height", height)
    .call(d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {{
        container.attr("transform", event.transform);
      }}));

const container = svg.append("g");

let currentLayout = "force";
let labelsVisible = true;
let simulation;

// Initialize force layout
function initForceLayout() {{
  simulation = d3.forceSimulation(graph.nodes)
    .force("link", d3.forceLink(graph.links).id(d => d.id).distance(120).strength(0.5))
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width/2, height/2))
    .force("collision", d3.forceCollide().radius(d => sizeScale(d.degree) + 10));
  
  simulation.on("tick", ticked);
}}

// Initialize hierarchy layout with better spacing
function initHierarchyLayout() {{
  const maxLevel = d3.max(graph.nodes, d => d.level);
  const levelHeight = (height - 100) / (maxLevel + 2);
  
  // Group nodes by level
  const nodesByLevel = d3.group(graph.nodes, d => d.level);
  
  nodesByLevel.forEach((nodes, level) => {{
    const y = levelHeight * (level + 1) + 50;
    
    // Calculate better horizontal spacing
    const nodesCount = nodes.length;
    const availableWidth = width - 100;
    const idealSpacing = 120; // Minimum spacing between nodes
    const totalNeededWidth = nodesCount * idealSpacing;
    
    if (totalNeededWidth > availableWidth) {{
      // If nodes don't fit in one row, arrange in a grid pattern
      const nodesPerRow = Math.floor(availableWidth / idealSpacing);
      const rows = Math.ceil(nodesCount / nodesPerRow);
      const rowHeight = 80;
      
      nodes.forEach((node, i) => {{
        const row = Math.floor(i / nodesPerRow);
        const col = i % nodesPerRow;
        const currentRowNodes = Math.min(nodesPerRow, nodesCount - row * nodesPerRow);
        const xSpacing = availableWidth / (currentRowNodes + 1);
        
        node.x = 50 + xSpacing * (col + 1);
        node.y = y + row * rowHeight;
        node.fx = node.x;
        node.fy = node.y;
      }});
    }} else {{
      // Fit in one row with even spacing
      const xSpacing = availableWidth / (nodesCount + 1);
      nodes.forEach((node, i) => {{
        node.x = 50 + xSpacing * (i + 1);
        node.y = y;
        node.fx = node.x;
        node.fy = node.y;
      }});
    }}
  }});
  
  simulation = d3.forceSimulation(graph.nodes)
    .force("link", d3.forceLink(graph.links).id(d => d.id).distance(100).strength(0.2))
    .force("collision", d3.forceCollide().radius(d => sizeScale(d.degree) + 15))
    .alpha(0.3);
  
  simulation.on("tick", ticked);
}}

const link = container.append("g")
  .selectAll("line")
  .data(graph.links)
  .enter().append("line")
    .attr("class", "link")
    .attr("stroke-width", d => Math.sqrt(d.value) * 1.5);

const node = container.append("g")
  .selectAll("circle")
  .data(graph.nodes)
  .enter().append("circle")
    .attr("class", d => d.degree === 0 ? "node isolated" : "node")
    .attr("r", d => d.degree === 0 ? 10 : sizeScale(d.degree))
    .attr("fill", d => d.degree === 0 ? "#666" : colorScale(d.level))
    .on("mouseover", showTooltip)
    .on("mousemove", moveTooltip)
    .on("mouseout", hideTooltip)
    .on("click", showDetails)
    .call(drag(simulation));

const labels = container.append("g")
  .selectAll("text")
  .data(graph.nodes)
  .enter().append("text")
    .attr("dy", d => -sizeScale(d.degree === 0 ? 1 : d.degree) - 8)
    .text(d => d.id);

// Initialize with force layout
initForceLayout();

function ticked() {{
  link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

  node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

  labels
      .attr("x", d => d.x)
      .attr("y", d => d.y);
}}

// Update statistics
function updateStats() {{
  const visibleNodes = graph.nodes.filter(d => !d.hidden).length;
  const maxLevel = d3.max(graph.nodes, d => d.level);
  const isolatedNodes = graph.nodes.filter(d => d.degree === 0).length;
  
  document.getElementById('stat-nodes').textContent = graph.nodes.length;
  document.getElementById('stat-edges').textContent = graph.links.length;
  document.getElementById('stat-visible').textContent = visibleNodes;
  document.getElementById('stat-levels').textContent = maxLevel + 1;
  document.getElementById('stat-isolated').textContent = isolatedNodes;
}}

updateStats();

// Layout controls
document.getElementById('force-layout').addEventListener('click', function() {{
  if (currentLayout === 'force') return;
  
  currentLayout = 'force';
  this.classList.add('active');
  document.getElementById('hierarchy-layout').classList.remove('active');
  
  // Reset fixed positions
  graph.nodes.forEach(d => {{
    d.fx = null;
    d.fy = null;
  }});
  
  simulation.stop();
  initForceLayout();
  simulation.alpha(1).restart();
}});

document.getElementById('hierarchy-layout').addEventListener('click', function() {{
  if (currentLayout === 'hierarchy') return;
  
  currentLayout = 'hierarchy';
  this.classList.add('active');
  document.getElementById('force-layout').classList.remove('active');
  
  simulation.stop();
  initHierarchyLayout();
  simulation.alpha(1).restart();
}});

// Toggle labels
document.getElementById('toggle-labels').addEventListener('click', function() {{
  labelsVisible = !labelsVisible;
  labels.style('display', labelsVisible ? 'block' : 'none');
  this.textContent = labelsVisible ? 'Hide Labels' : 'Show Labels';
}});

// Reset view
document.getElementById('reset-view').addEventListener('click', function() {{
  svg.transition().duration(750).call(
    d3.zoom().transform,
    d3.zoomIdentity
  );
  
  node.attr("class", d => d.degree === 0 ? "node isolated" : "node");
  link.attr("class", "link");
  closePanel();
}});

// Connection filter
const filterSlider = document.getElementById('connection-filter');
const filterValue = document.getElementById('filter-value');

filterSlider.addEventListener('input', function() {{
  const minConnections = parseInt(this.value);
  filterValue.textContent = minConnections;
  
  node.each(function(d) {{
    d.hidden = d.degree < minConnections;
  }});
  
  node.style('display', d => d.hidden ? 'none' : 'block');
  labels.style('display', d => d.hidden || !labelsVisible ? 'none' : 'block');
  
  link.style('display', d => {{
    return d.source.hidden || d.target.hidden ? 'none' : 'block';
  }});
  
  updateStats();
}});

// Search functionality
const searchInput = document.getElementById('search-input');
searchInput.addEventListener('input', function() {{
  const searchTerm = this.value.toLowerCase().trim();
  
  if (searchTerm === '') {{
    node.classed('dimmed', false).classed('highlighted', false);
    link.classed('highlighted', false);
    return;
  }}
  
  node.classed('dimmed', d => !d.id.toLowerCase().includes(searchTerm));
  node.classed('highlighted', d => d.id.toLowerCase().includes(searchTerm));
  
  // Highlight edges between matched nodes
  link.classed('highlighted', d => {{
    const sourceMatch = d.source.id.toLowerCase().includes(searchTerm);
    const targetMatch = d.target.id.toLowerCase().includes(searchTerm);
    return sourceMatch && targetMatch;
  }});
}});

function showTooltip(event, d) {{
  const tooltip = d3.select("#tooltip");
  const context = d.contexts.third_person || "No description available";
  
  let statusInfo = '';
  if (d.degree === 0) {{
    statusInfo = '<div style="color: #ffa94d; margin-top: 8px;">⚠️ Isolated node (no connections)</div>';
  }}
  
  tooltip
    .style("display", "block")
    .html(`
      <div class="title">${{d.id}}</div>
      <div>${{context}}</div>
      <div class="metrics">
        Level: ${{d.level}} | Connections: ${{d.degree}} (↑${{d.incoming}} ↓${{d.outgoing}})
      </div>
      ${{statusInfo}}
    `);
}}

function moveTooltip(event) {{
  d3.select("#tooltip")
    .style("left", (event.pageX + 15) + "px")
    .style("top", (event.pageY + 15) + "px");
}}

function hideTooltip() {{
  d3.select("#tooltip").style("display", "none");
}}

function showDetails(event, d) {{
  // Reset all highlighting
  node.each(function(n) {{
    d3.select(this).attr("class", n.degree === 0 ? "node isolated" : "node");
  }});
  link.attr("class", "link");
  
  // Highlight clicked node
  d3.select(event.target).attr("class", "node highlighted");
  
  // Find all connected nodes (both directions)
  const connectedNodeIds = new Set(d.children);
  
  // Find incoming relationships
  graph.links.forEach(l => {{
    if (l.target.id === d.id) connectedNodeIds.add(l.source.id);
    if (l.source.id === d.id) connectedNodeIds.add(l.target.id);
  }});
  
  // Dim non-connected nodes
  node.each(function(n) {{
    if (n.id === d.id) return;
    if (connectedNodeIds.has(n.id)) {{
      d3.select(this).attr("class", "node connected");
    }} else {{
      d3.select(this).attr("class", "node dimmed");
    }}
  }});
  
  link.each(function(l) {{
    if ((l.source.id === d.id && connectedNodeIds.has(l.target.id)) ||
        (l.target.id === d.id && connectedNodeIds.has(l.source.id))) {{
      d3.select(this).attr("class", "link highlighted");
    }}
  }});
  
  // Show info panel
  const panel = document.getElementById("info-panel");
  const content = document.getElementById("panel-content");
  
  let html = `
    <h2>${{d.id}}</h2>
    <div style="margin-bottom: 20px;">
      <span class="metric-badge">Level ${{d.level}}</span>
      <span class="metric-badge">↔ ${{d.degree}} Connections</span>
      <span class="metric-badge">↑ ${{d.incoming}} In</span>
      <span class="metric-badge">↓ ${{d.outgoing}} Out</span>
    </div>
  `;
  
  // Warning for isolated nodes
  if (d.degree === 0) {{
    html += `
      <div class="warning-badge">
        ⚠️ This node has no connections in the graph
      </div>
    `;
  }}
  
  // Show all three contexts
  if (d.contexts.first_person) {{
    html += `
      <div class="context-section">
        <h3>📝 First Person Perspective</h3>
        <p>${{d.contexts.first_person}}</p>
      </div>
    `;
  }}
  
  if (d.contexts.second_person) {{
    html += `
      <div class="context-section">
        <h3>👤 Second Person Perspective</h3>
        <p>${{d.contexts.second_person}}</p>
      </div>
    `;
  }}
  
  if (d.contexts.third_person) {{
    html += `
      <div class="context-section">
        <h3>🌍 Third Person Perspective</h3>
        <p>${{d.contexts.third_person}}</p>
      </div>
    `;
  }}
  
  // Show outgoing relationships
  if (d.children && d.children.length > 0) {{
    html += `
      <h3>🔗 Outgoing Relationships (${{d.children.length}})</h3>
      <div class="children-list">
        ${{d.children.map(child => 
          `<span class="child-tag" onclick="searchAndShow('${{child}}')">${{child}}</span>`
        ).join('')}}
      </div>
    `;
  }}
  
  // Find incoming relationships
  const incoming = [];
  for (const [key, value] of Object.entries(fullKG)) {{
    if (value.children && value.children.includes(d.id)) {{
      incoming.push(key);
    }}
  }}
  
  if (incoming.length > 0) {{
    html += `
      <h3>🔙 Incoming Relationships (${{incoming.length}})</h3>
      <div class="children-list">
        ${{incoming.map(parent => 
          `<span class="child-tag" onclick="searchAndShow('${{parent}}')">${{parent}}</span>`
        ).join('')}}
      </div>
    `;
  }}
  
  // If no relationships at all
  if (d.children.length === 0 && incoming.length === 0) {{
    html += `
      <div style="padding: 20px; text-align: center; color: #aaa; font-style: italic;">
        This concept appears to be isolated in the knowledge graph.<br>
        It may need more connections or could be a data quality issue.
      </div>
    `;
  }}
  
  content.innerHTML = html;
  panel.style.display = "block";
}}

function searchAndShow(nodeId) {{
  const nodeData = graph.nodes.find(n => n.id === nodeId);
  if (!nodeData) return;
  
  // Find the node element
  const nodeElement = node.filter(d => d.id === nodeId).node();
  if (nodeElement) {{
    showDetails({{ target: nodeElement }}, nodeData);
    
    // Center on node
    const transform = d3.zoomIdentity
      .translate(width / 2, height / 2)
      .scale(1.5)
      .translate(-nodeData.x, -nodeData.y);
    
    svg.transition().duration(750).call(
      d3.zoom().transform,
      transform
    );
  }}
}}

function closePanel() {{
  document.getElementById("info-panel").style.display = "none";
  node.each(function(d) {{
    d3.select(this).attr("class", d.degree === 0 ? "node isolated" : "node");
  }});
  link.attr("class", "link");
}}

function drag(simulation) {{
  function dragstarted(event, d) {{
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }}

  function dragged(event, d) {{
    d.fx = event.x;
    d.fy = event.y;
  }}

  function dragended(event, d) {{
    if (!event.active) simulation.alphaTarget(0);
    if (currentLayout !== 'hierarchy') {{
      d.fx = null;
      d.fy = null;
    }}
  }}

  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}}

</script>
</body>
"""
    return html


def main():
    print("[Viz] Loading KG...")
    kg = json.load(open(INPUT))

    print("[Viz] Building D3 graph with hierarchy...")
    d3_data = build_d3_graph(kg)

    print("[Viz] Writing HTML...")
    html = generate_html(d3_data, kg)

    with open(OUTPUT, "w") as f:
        f.write(html)

    print(f"[Viz] Enhanced visualization written to {OUTPUT}")
    print("\n✨ Fixed Issues:")
    print("  ✓ Isolated nodes (like 'pressure') now highlighted with orange dashed border")
    print("  ✓ Fixed panel overlap on bottom left")
    print("  ✓ Improved hierarchy layout with better spacing and multi-row support")
    print("  ✓ Better label contrast with enhanced text shadow")
    print("  ✓ Added isolated nodes counter in statistics")
    print("\nOpen the HTML file in your browser to explore!")


if __name__ == "__main__":
    main()