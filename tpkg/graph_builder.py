import json
import os
from tpkg.noun_extractor import extract_nouns
from tpkg.context_generator import generate_contexts
from tpkg.logger import log

CHECKPOINT_FILE = "kg_checkpoint.json"


# ---------------------------------------------------------
# Save checkpoint after each noun is processed
# ---------------------------------------------------------
def save_checkpoint(graph):
    """Write current KG to checkpoint file."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(graph, f, indent=2)
    log("[KG] Checkpoint saved.", depth=0)



# ---------------------------------------------------------
# Main KG Builder Class
# ---------------------------------------------------------
class ContextualKG:

    def __init__(self):
        self.graph = {}
        self.processed = set()

        # ---------- LOAD CHECKPOINT IF EXISTS ----------
        if os.path.exists(CHECKPOINT_FILE):
            log("[KG] Loading checkpoint...", depth=0)
            with open(CHECKPOINT_FILE, "r") as f:
                self.graph = json.load(f)
            self.processed = set(self.graph.keys())
            log(f"[KG] Restored {len(self.graph)} nodes from checkpoint.", depth=0)
        else:
            log("[KG] No checkpoint detected. Starting fresh.", depth=0)


    # -----------------------------------------------------
    # Add new noun node to graph
    # -----------------------------------------------------
    def add_node(self, noun, contexts):
        if noun not in self.graph:
            self.graph[noun] = {
                "contexts": contexts,
                "children": []
            }


    # -----------------------------------------------------
    # Build full KG from paragraph
    # -----------------------------------------------------
    def build(self, paragraph):
        """Build a contextual knowledge graph."""

        log("[KG] Extracting base nouns from paragraph...", depth=0)
        base_nouns = extract_nouns(paragraph)
        log(f"[KG] Base nouns found: {base_nouns}", depth=0)

        for noun in base_nouns:
            self.process_noun(noun, paragraph, depth=0)

        return self.graph


    # -----------------------------------------------------
    # Core recursive noun processor
    # -----------------------------------------------------
    def process_noun(self, noun, paragraph, depth, max_depth=2):
        """
        Recursive noun processing with:
          - color logs
          - caching
          - checkpoint saving
        """

        # Skip if processed previously
        if noun in self.processed:
            log(f"[KG] Skipping already processed noun: {noun}", depth)
            return

        # Mark processed
        log(f"[KG] Processing noun: {noun} (depth={depth})", depth)
        self.processed.add(noun)

        # ---------- LLM CALL (cached) ----------
        log(f"[KG]  → Calling LLM for contexts of noun: {noun}", depth)
        contexts = generate_contexts(noun, paragraph)

        # Save node to graph
        self.add_node(noun, contexts)

        # ---------- SAVE CHECKPOINT ----------
        save_checkpoint(self.graph)

        # ---------- Extract child nouns ----------
        combined = (
            contexts["second_person"] + " " +
            contexts["first_person"] + " " +
            contexts["third_person"]
        )

        new_nouns = extract_nouns(combined)
        self.graph[noun]["children"] = new_nouns

        log(f"[KG]  → Found child nouns for '{noun}': {new_nouns}", depth)

        # ---------- RECURSION ----------
        if depth < max_depth:
            for child in new_nouns:
                self.process_noun(child, combined, depth + 1, max_depth)
        else:
            log(f"[KG] Reached max depth for noun: {noun}", depth)



def save_graph(graph, filename="kg_output.json"):
    """Save final KG to a specified JSON file."""
    with open(filename, "w") as f:
        json.dump(graph, f, indent=2)
    log(f"[KG] Final KG saved to: {filename}", depth=0)

