# main.py
from tpkg.graph_builder import ContextualKG, save_checkpoint, save_graph

# ------- SAMPLE INPUT TEXT -------
sample_paragraph = """
Robots are widely used in modern warehouses to automate the movement of goods.
A robot can pick items from shelves, transport crates, and assist human workers.
Warehouse managers rely on robots to improve efficiency and reduce operational cost.
"""

def main():

    kg = ContextualKG()

    graph = kg.build(sample_paragraph)

    save_checkpoint(graph)

    # Save final KG
    save_graph(graph, "kg_output.json")

    # print a small preview to console for quick sanity-check
    # (show first 3 nouns only to avoid dumping full graph on screen)

    print("\n=== PREVIEW OF BUILT KNOWLEDGE GRAPH ===")
    for i, noun in enumerate(graph.keys()):
        if i >= 3:
            break
        print(f"\nNOUN: {noun}")
        print("CONTEXTS:")
        print(f" - 2P: {graph[noun]['contexts']['second_person']}")
        print(f" - 1P: {graph[noun]['contexts']['first_person']}")
        print(f" - 3P: {graph[noun]['contexts']['third_person']}")

    print("\nFull KG saved to: kg_output.json\n")

if __name__ == "__main__":
    # Python entrypoint mechanism → runs main() when file is executed directly
    main()






