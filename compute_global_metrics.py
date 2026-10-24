"""
compute_global_metrics.py
=========================
Standalone helper: loads the pre-built global AUTHOR graph and (re-)computes
the node-level metrics, then saves global_node_metrics.pkl.

Graph: Author Citation Network (1992-2002)
  - Node  = author name (string)
  - Edge A->B = author A was cited by author B (influence direction)

Run this only if you need to recompute metrics without re-parsing the raw file.
The main end-to-end pipeline is in build_global_graph.py.
"""

import os
import pickle
import time
import networkx as nx

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, "outp")
os.makedirs(OUTPUT_DIR, exist_ok=True)

GRAPH_PATH  = os.path.join(OUTPUT_DIR, "global_graph_1992_2002.pkl")
METRICS_OUT = os.path.join(OUTPUT_DIR, "global_node_metrics.pkl")


def compute_and_save(graph_path: str, metrics_path: str):
    print(f"--> Loading graph from '{graph_path}' ...")
    with open(graph_path, "rb") as f:
        G: nx.DiGraph = pickle.load(f)
    print(f"    Loaded: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    print("--> Computing in-degree / out-degree ...")
    in_deg  = dict(G.in_degree())
    out_deg = dict(G.out_degree())

    print("--> Computing PageRank (alpha=0.85, max_iter=100) ...")
    t0 = time.time()
    try:
        pageranks = nx.pagerank_scipy(G, alpha=0.85, max_iter=100, tol=1.0e-6)
    except AttributeError:
        # NetworkX >= 3.x removed pagerank_scipy
        pageranks = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1.0e-6)
    print(f"    PageRank done in {time.time()-t0:.1f}s")

    metrics = {
        node: {
            "in_degree":  in_deg.get(node, 0),
            "out_degree": out_deg.get(node, 0),
            "pagerank":   pageranks.get(node, 0.0),
        }
        for node in G.nodes()
    }

    print(f"--> Saving metrics -> '{metrics_path}' ...")
    with open(metrics_path, "wb") as f:
        pickle.dump(metrics, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"==> Done. Metrics for {len(metrics):,} nodes saved.")

    # Quick sanity check
    sample = list(metrics.items())[:3]
    for nid, m in sample:
        print(f"    '{nid}': in={m['in_degree']}, out={m['out_degree']}, pr={m['pagerank']:.6f}")


if __name__ == "__main__":
    compute_and_save(GRAPH_PATH, METRICS_OUT)
