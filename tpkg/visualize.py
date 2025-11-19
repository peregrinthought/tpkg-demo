# visualize.py
import json

INPUT = "kg_output.json"
OUTPUT = "kg_visualizer.html"


def build_d3_graph(kg):
    MAX_EDGES_PER_NODE = 5
    nodes = []
    
    # Build nodes with full context data
    for noun, data in kg.items():
        nodes.append({
            "id": noun,
            "contexts": data.get("contexts", {}),
            "children": data.get("children", [])
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
                "target": child
            })

    return {"nodes": nodes, "links": links}


def generate_html(d3_data, kg):
    """
    Enhanced visualization with:
      - Hover tooltips showing context
      - Click to see full details in side panel
      - Highlight connected nodes
      - Show relationships
    """

    html = f"""
<!DOCTYPE html>
<meta charset="utf-8">
<style>
  body {{ 
    margin: 0; 
    background: #111; 
    font-family: Arial, sans-serif;
    overflow: hidden;
  }}
  
  #graph-container {{
    position: relative;
    width: 100vw;
    height: 100vh;
  }}
  
  #info-panel {{
    position: absolute;
    top: 20px;
    right: 20px;
    width: 350px;
    max-height: 90vh;
    background: rgba(30, 30, 30, 0.95);
    border: 2px solid #4aa3ff;
    border-radius: 8px;
    padding: 20px;
    color: #fff;
    overflow-y: auto;
    display: none;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  
  #info-panel h2 {{
    margin-top: 0;
    color: #4aa3ff;
    border-bottom: 2px solid #4aa3ff;
    padding-bottom: 10px;
  }}
  
  #info-panel h3 {{
    color: #6bc5ff;
    margin-top: 20px;
    margin-bottom: 10px;
    font-size: 14px;
  }}
  
  #info-panel p {{
    line-height: 1.6;
    margin: 8px 0;
    font-size: 13px;
  }}
  
  #info-panel .context-section {{
    background: rgba(50, 50, 50, 0.5);
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
    border-left: 3px solid #4aa3ff;
  }}
  
  #info-panel .children-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }}
  
  #info-panel .child-tag {{
    background: #4aa3ff;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    display: inline-block;
  }}
  
  .close-btn {{
    position: absolute;
    top: 15px;
    right: 15px;
    background: #ff4444;
    border: none;
    color: white;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }}
  
  .close-btn:hover {{
    background: #ff6666;
  }}
  
  text {{ 
    fill: #fff; 
    font-family: Arial; 
    font-size: 12px; 
    pointer-events: none;
    text-shadow: 1px 1px 2px #000;
  }}
  
  .link {{ 
    stroke: #555; 
    stroke-opacity: 0.6; 
    stroke-width: 1.5px;
  }}
  
  .link.highlighted {{
    stroke: #4aa3ff;
    stroke-opacity: 1;
    stroke-width: 3px;
  }}
  
  .node {{ 
    fill: #4aa3ff; 
    stroke: #fff; 
    stroke-width: 2px; 
    cursor: pointer;
    transition: all 0.3s;
  }}
  
  .node:hover {{
    fill: #6bc5ff;
    r: 12;
  }}
  
  .node.highlighted {{
    fill: #ff6b6b;
    stroke: #fff;
    stroke-width: 3px;
  }}
  
  .node.connected {{
    fill: #ffd93d;
    stroke: #fff;
    stroke-width: 2px;
  }}
  
  .tooltip {{
    position: absolute;
    background: rgba(20, 20, 20, 0.95);
    color: #fff;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #4aa3ff;
    pointer-events: none;
    font-size: 12px;
    max-width: 300px;
    display: none;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.5);
  }}
  
  .tooltip .title {{
    font-weight: bold;
    color: #4aa3ff;
    margin-bottom: 8px;
    font-size: 14px;
  }}
  
  #instructions {{
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(30, 30, 30, 0.9);
    color: #fff;
    padding: 15px;
    border-radius: 6px;
    border: 1px solid #4aa3ff;
    font-size: 12px;
    max-width: 250px;
  }}
  
  #instructions h4 {{
    margin-top: 0;
    color: #4aa3ff;
  }}
  
  #instructions ul {{
    margin: 5px 0;
    padding-left: 20px;
  }}
</style>
<body>

<div id="graph-container">
  <svg id="graph"></svg>
  
  <div id="instructions">
    <h4>🔍 Instructions</h4>
    <ul>
      <li><strong>Hover</strong> over nodes to see context</li>
      <li><strong>Click</strong> nodes for full details</li>
      <li><strong>Drag</strong> nodes to reposition</li>
    </ul>
  </div>
  
  <div id="info-panel">
    <button class="close-btn" onclick="closePanel()">×</button>
    <div id="panel-content"></div>
  </div>
  
  <div class="tooltip" id="tooltip"></div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>

const graph = {json.dumps(d3_data)};
const fullKG = {json.dumps(kg)};

const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#graph")
    .attr("width", width)
    .attr("height", height);

const simulation = d3.forceSimulation(graph.nodes)
    .force("link", d3.forceLink(graph.links).id(d => d.id).distance(100).strength(0.3))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width/2, height/2))
    .force("collision", d3.forceCollide().radius(30));

const link = svg.append("g")
  .selectAll("line")
  .data(graph.links)
  .enter().append("line")
    .attr("class", "link");

const node = svg.append("g")
  .selectAll("circle")
  .data(graph.nodes)
  .enter().append("circle")
    .attr("r", 8)
    .attr("class", "node")
    .on("mouseover", showTooltip)
    .on("mousemove", moveTooltip)
    .on("mouseout", hideTooltip)
    .on("click", showDetails)
    .call(drag(simulation));

const labels = svg.append("g")
  .selectAll("text")
  .data(graph.nodes)
  .enter().append("text")
    .attr("dy", -12)
    .text(d => d.id);

simulation.on("tick", () => {{
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
}});

function showTooltip(event, d) {{
  const tooltip = d3.select("#tooltip");
  const context = d.contexts.third_person || "No description available";
  
  tooltip
    .style("display", "block")
    .html(`
      <div class="title">${{d.id}}</div>
      <div>${{context}}</div>
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
  node.attr("class", "node");
  link.attr("class", "link");
  
  // Highlight clicked node
  d3.select(event.target).attr("class", "node highlighted");
  
  // Highlight connected nodes and edges
  const connectedNodeIds = new Set(d.children);
  
  node.each(function(n) {{
    if (connectedNodeIds.has(n.id)) {{
      d3.select(this).attr("class", "node connected");
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
  
  let html = `<h2>${{d.id}}</h2>`;
  
  // Show all three contexts
  if (d.contexts.first_person) {{
    html += `
      <div class="context-section">
        <h3>📝 First Person View</h3>
        <p>${{d.contexts.first_person}}</p>
      </div>
    `;
  }}
  
  if (d.contexts.second_person) {{
    html += `
      <div class="context-section">
        <h3>👤 Second Person View</h3>
        <p>${{d.contexts.second_person}}</p>
      </div>
    `;
  }}
  
  if (d.contexts.third_person) {{
    html += `
      <div class="context-section">
        <h3>🌍 Third Person View</h3>
        <p>${{d.contexts.third_person}}</p>
      </div>
    `;
  }}
  
  // Show relationships
  if (d.children && d.children.length > 0) {{
    html += `
      <h3>🔗 Connected Concepts (Relationships)</h3>
      <div class="children-list">
        ${{d.children.map(child => `<span class="child-tag">${{child}}</span>`).join('')}}
      </div>
    `;
  }}
  
  content.innerHTML = html;
  panel.style.display = "block";
}}

function closePanel() {{
  document.getElementById("info-panel").style.display = "none";
  // Reset highlighting
  node.attr("class", "node");
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
    d.fx = null;
    d.fy = null;
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

    print("[Viz] Building D3 graph...")
    d3_data = build_d3_graph(kg)

    print("[Viz] Writing HTML...")
    html = generate_html(d3_data, kg)

    with open(OUTPUT, "w") as f:
        f.write(html)

    print(f"[Viz] Visualization written to {OUTPUT}")
    print("Open this file in your browser to view the interactive graph.")


if __name__ == "__main__":
    main()