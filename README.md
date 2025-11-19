# Tri-Perspective Knowledge Graph — Demo

This project builds a **multi-view knowledge graph** using three complementary perspectives for each noun extracted from text:

- **Second-person context** — how *you* interact with the noun  
- **First-person (internal) context** — what the noun “experiences” internally  
- **Third-person situational context** — the noun’s role *inside the paragraph*  

The graph is recursively expanded and visualized using an interactive **D3 force layout**.

---

## Setup Your OpenAI API Key

Before running anything, you **must create a `.env` file** in the project root:
OPENAI_API_KEY=your_key_here

> ⚠️ **Do NOT commit this file to GitHub.**  
> Your `.env` is automatically read by the project (`tpkg/utils.py` + `dotenv`).

---

## 🔧 Prerequisites

(Optional but recommended) Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
````

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download the spaCy English model

```bash
python -m spacy download en_core_web_sm
```

---

## How to Use

### **Step 1 — Add your input text**

Open `main.py` and edit the `sample_paragraph` variable:

```python
sample_paragraph = """
Your paragraph here...
"""
```

---

### **Step 2 — Build the Knowledge Graph**

```bash
python main.py
```

This step performs:

* noun extraction
* tri-perspective context generation
* recursive child-noun expansion
* caching for repeated nouns
* checkpointing into `kg_checkpoint.json`
* final graph output to `kg_output.json`

---

### **Step 3 — Generate Visualization**

```bash
python tpkg/visualize.py
```

This writes the file:

```
kg_visualizer.html
```

---

### **Step 4 — View the Graph**

Open `kg_visualizer.html` in your browser.

You can:

* drag nodes
* explore clusters
* inspect neighborhood structure
* visually understand contextual density and relationships

---

## 🧠 What Is This?

**Tri-Perspective Knowledge Graph (TPKG)** is an experimental system that converts text into an **agent-usable, cognitively structured world model**.

Traditional KGs store only relationships like:

```
(noun) — (verb) → (noun)
```

TPKG instead generates **three cognitive lenses**:

### **1. Second-Person Lens (You → Concept)**

How a user or agent interacts with the concept; *affordances* and usability.

### **2. First-Person Lens (Concept → Self)**

The "internal life" of the concept—what it does, feels, or undergoes.

### **3. Third-Person Situational Lens (Concept → Environment)**

What role the concept plays in the described situation or system.

By recursively following nouns across generated contexts, TPKG forms a **living, contextual world model** — useful for:

* agent reasoning
* narrative consistency
* affordance modeling
* environment simulation
* planning and decision graphs
* grounding LLMs in context-aware structures

In short:
**This is a step toward turning text into a world model that agents can use.**

---

## 📁 Project Outputs

* `kg_checkpoint.json` — autosaved graph for crash recovery
* `kg_output.json` — final KG
* `kg_visualizer.html` — interactive graph explorer
