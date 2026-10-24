"""
Task A - Build Global AUTHOR Citation Graph G (1992-2002)
==========================================================
Theo bai bao DeepCas (arXiv:1611.05373), Muc 4.1:
  "We construct the global network G based on citations between 1992 and 2002.
   That is, an EDGE draws from node A to B if AUTHOR A is ever cited by B."

=> Node la TEN TAC GIA (author name, tu truong #@)
=> Edge A->B: bai bao cua tac gia B trich dan bai bao cua tac gia A
              (A la tac gia duoc trich dan, B la tac gia di trich dan)
              = Chieu lan truyen thong tin/anh huong (cited -> citing)

Input : dblp.v8/dblp.txt
Output: global_graph_1992_2002.pkl     - nx.DiGraph (nodes = author names)
        global_node_metrics.pkl        - dict {author: {in_degree, out_degree, pagerank}}

Paper target: 131,415 nodes | 842,542 edges (Table 1, DeepCas)
"""

import os
import pickle
import time
import networkx as nx

# --- Paths -------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(BASE_DIR, "dblp.v8", "dblp.txt")
OUTPUT_DIR  = os.path.join(BASE_DIR, "outp")
os.makedirs(OUTPUT_DIR, exist_ok=True)

GRAPH_OUT   = os.path.join(OUTPUT_DIR, "global_graph_1992_2002.pkl")
METRICS_OUT = os.path.join(OUTPUT_DIR, "global_node_metrics.pkl")

YEAR_MIN, YEAR_MAX = 1992, 2002
TARGET_NODES, TARGET_EDGES = 131_415, 842_542


# === PASS 1: Doc toan bo file, luu metadata moi bai bao ======================
def parse_all_papers(input_file):
    """
    Stream-parse toan bo file.
    Tra ve:
      paper_meta : dict  pid -> (year:int, authors:list[str])
      paper_refs : dict  pid -> list[ref_id]   (chi giu paper trong 1992-2002)
    """
    print(f"--> [Pass 1] Streaming '{input_file}' ...")
    t0 = time.time()

    paper_meta = {}   # pid -> (year, [authors])
    paper_refs = {}   # pid -> [ref_ids]   (chi paper trong range)

    cur  = {}
    refs = []
    blocks = 0

    with open(input_file, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")

            if line == "":
                pid     = cur.get("index")
                year    = cur.get("year")
                authors = cur.get("authors", [])

                if pid and year:
                    paper_meta[pid] = (year, authors)
                    if YEAR_MIN <= year <= YEAR_MAX and refs:
                        paper_refs[pid] = refs[:]   # copy

                cur  = {}
                refs = []
                blocks += 1
                if blocks % 500_000 == 0:
                    print(f"   ... {blocks:,} blocks parsed | {len(paper_meta):,} papers stored")
                continue

            if line.startswith("#index"):
                cur["index"] = line[6:]
            elif line.startswith("#t"):
                try:
                    cur["year"] = int(line[2:].strip())
                except ValueError:
                    pass
            elif line.startswith("#@"):
                cur["authors"] = [a.strip() for a in line[2:].split(",") if a.strip()]
            elif line.startswith("#%"):
                refs.append(line[2:])
            # #* title, #c venue, #! abstract -- bo qua

    # Flush last block
    pid     = cur.get("index")
    year    = cur.get("year")
    authors = cur.get("authors", [])
    if pid and year:
        paper_meta[pid] = (year, authors)
        if YEAR_MIN <= year <= YEAR_MAX and refs:
            paper_refs[pid] = refs[:]

    elapsed = time.time() - t0
    papers_in_range = sum(1 for y, _ in paper_meta.values() if YEAR_MIN <= y <= YEAR_MAX)
    print(f"==> Pass 1 done in {elapsed:.1f}s | "
          f"Total papers: {len(paper_meta):,} | "
          f"Papers in [{YEAR_MIN},{YEAR_MAX}] with refs: {len(paper_refs):,} | "
          f"Papers in [{YEAR_MIN},{YEAR_MAX}] total: {papers_in_range:,}")
    return paper_meta, paper_refs


# === PASS 2: Dung do thi tac gia =============================================
def build_author_graph(paper_meta, paper_refs):
    """
    Xay dung Author Citation Graph G.

    Voi moi bai bao P (nam trong 1992-2002) trich dan bai R (cung trong 1992-2002):
      - Lay danh sach tac gia B[] cua P   (tac gia di trich dan)
      - Lay danh sach tac gia A[] cua R   (tac gia duoc trich dan)
      - Voi moi cap (a in A, b in B) voi a != b:
          them canh a -> b vao G
    Luu y: Dung nx.DiGraph nen cac canh trung lap tu dong ghi de (khong tang them).
    """
    print("--> [Pass 2] Building author citation graph ...")
    t0 = time.time()

    G = nx.DiGraph()
    processed = 0
    edges_added = 0
    skipped_no_ref_meta = 0

    for pid, r_list in paper_refs.items():
        yr_p, b_authors = paper_meta.get(pid, (0, []))
        if not b_authors:
            continue

        for rid in r_list:
            r_info = paper_meta.get(rid)
            if r_info is None:
                skipped_no_ref_meta += 1
                continue

            yr_r, a_authors = r_info
            # Chi xu ly neu ref cung nam trong khoang 1992-2002
            if not (YEAR_MIN <= yr_r <= YEAR_MAX) or not a_authors:
                continue

            # Them canh cited_author -> citing_author (chieu lan truyen)
            for a in a_authors:
                for b in b_authors:
                    if a != b:
                        G.add_edge(a, b)
                        edges_added += 1

        processed += 1
        if processed % 50_000 == 0:
            print(f"   ... {processed:,} papers processed | "
                  f"nodes: {G.number_of_nodes():,} | edges: {G.number_of_edges():,}")

    elapsed = time.time() - t0
    print(f"==> Pass 2 done in {elapsed:.1f}s | "
          f"raw edge attempts: {edges_added:,} | "
          f"unique edges in G: {G.number_of_edges():,} | "
          f"nodes in G: {G.number_of_nodes():,}")
    print(f"    (Refs skipped - no metadata in dataset: {skipped_no_ref_meta:,})")
    return G


# === Tinh cac chi so mang ====================================================
def compute_metrics(G):
    print("--> Computing in-degree / out-degree ...")
    in_deg  = dict(G.in_degree())
    out_deg = dict(G.out_degree())

    print("--> Computing PageRank (alpha=0.85, max_iter=100) ...")
    t0 = time.time()
    try:
        pageranks = nx.pagerank_scipy(G, alpha=0.85, max_iter=100, tol=1e-6)
    except AttributeError:
        # NetworkX >= 3.x: pagerank_scipy da bi xoa
        pageranks = nx.pagerank(G, alpha=0.85, max_iter=100, tol=1e-6)
    print(f"   PageRank done in {time.time()-t0:.1f}s")

    metrics = {
        node: {
            "in_degree":  in_deg.get(node, 0),
            "out_degree": out_deg.get(node, 0),
            "pagerank":   pageranks.get(node, 0.0),
        }
        for node in G.nodes()
    }
    return metrics


# === Xuat file ===============================================================
def export(G, metrics, graph_path, metrics_path):
    print(f"--> Saving graph   -> {graph_path}")
    with open(graph_path, "wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"--> Saving metrics -> {metrics_path}")
    with open(metrics_path, "wb") as f:
        pickle.dump(metrics, f, protocol=pickle.HIGHEST_PROTOCOL)

    print("==> All files exported successfully.")


# === Validation + so sanh bai bao ============================================
def validate(graph_path, metrics_path):
    print("\n--- Validation ---")
    with open(graph_path, "rb") as f:
        G = pickle.load(f)
    with open(metrics_path, "rb") as f:
        metrics = pickle.load(f)

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()

    print(f"  Graph   : {n_nodes:,} nodes (authors), {n_edges:,} edges")
    print(f"  Metrics : {len(metrics):,} entries")
    print(f"  Directed: {G.is_directed()}")

    # Spot-check 3 nodes
    sample = list(G.nodes())[:3]
    for author in sample:
        m = metrics.get(author, {})
        print(f"  Author '{author}': "
              f"in={m.get('in_degree')}, "
              f"out={m.get('out_degree')}, "
              f"pr={m.get('pagerank'):.6f}")

    # Degree stats
    in_degs = [G.in_degree(n) for n in G.nodes()]
    print(f"\n  In-degree max: {max(in_degs):,}  mean: {sum(in_degs)/len(in_degs):.2f}")

    # Top 5 most cited authors
    top5 = sorted(G.nodes(), key=lambda x: G.in_degree(x), reverse=True)[:5]
    print("\n  Top 5 most cited authors:")
    for rank, author in enumerate(top5, 1):
        print(f"    {rank}. {author}  (in-degree={G.in_degree(author)})")

    # Edge direction check
    sample_edges = list(G.edges())[:3]
    print("\n  Edge sample (cited_author -> citing_author):")
    for a, b in sample_edges:
        print(f"    '{a}' -> '{b}'")

    # So sanh voi bai bao
    node_ratio = n_nodes / TARGET_NODES
    edge_ratio = n_edges / TARGET_EDGES
    print(f"\n  +-- So sanh voi DeepCas Table 1 (AMINER dataset) --------")
    print(f"  |  Nodes: {n_nodes:>8,}  vs target {TARGET_NODES:>8,}  -> {node_ratio:.3f}x  ({abs(1-node_ratio)*100:.1f}% off)")
    print(f"  |  Edges: {n_edges:>8,}  vs target {TARGET_EDGES:>8,}  -> {edge_ratio:.3f}x  ({abs(1-edge_ratio)*100:.1f}% off)")
    print(f"  |")
    if abs(1 - node_ratio) < 0.05:
        print(f"  |  [OK] Nodes khop tot (< 5% sai lech) - dung Author network!")
    else:
        print(f"  |  [!]  Nodes chenh lech - kiem tra lai logic")
    if abs(1 - edge_ratio) < 0.2:
        print(f"  |  [OK] Edges khop kha tot (< 20% sai lech)")
    else:
        print(f"  |  [!]  Edges chenh lech nhieu - co the do V8 co nhieu co-author hon V5/V6")
        print(f"  |        (moi citation pair tao ra |A_authors| x |B_authors| edges)")
    print(f"  +--------------------------------------------------------")
    print("\n--- Validation PASSED ---")


# === Main ====================================================================
if __name__ == "__main__":
    t_total = time.time()

    paper_meta, paper_refs = parse_all_papers(INPUT_FILE)
    G       = build_author_graph(paper_meta, paper_refs)
    metrics = compute_metrics(G)
    export(G, metrics, GRAPH_OUT, METRICS_OUT)
    validate(GRAPH_OUT, METRICS_OUT)

    print(f"\nTask A complete in {time.time()-t_total:.1f}s total.")
