r"""
visualize_global_graph.py
=========================
Truc quan hoa toan dien do thi tac gia (Author Citation Graph G) va cac chi so Task A:
  - global_graph_1992_2002.pkl (133,857 nodes, 2,266,378 edges)
  - global_node_metrics.pkl (in_degree, out_degree, pagerank)

Noi dung truc quan hoa:
  1. So sanh truc dien voi Paper DeepCas (Table 1):
     - Nodes: 133,857 vs 131,415 (Khop 98.2%)
     - Edges: 2,266,378 (Author pairs) vs 842,542 (Paper target) vs 718k-931k (Raw paper citations)
  2. Top 20 tac gia duoc trich dan nhieu nhat (In-Degree)
  3. Top 20 tac gia theo chi so PageRank toan cuc
  4. Phan phoi In-Degree & Out-Degree (Log-Log scale -> Power-law)
  5. Tuong quan In-Degree vs PageRank (Scatter plot)
  6. Mang luoi cuc bo (Ego-network 2D) cua hoc gia dung dau (Philip S. Yu)

Dau ra:
  - outp/global_graph_dashboard.html (Interactive HTML offline, tu nhung Plotly JS)
  - outp/global_graph_static.png     (Static 6-panel PNG chat luong cao)
"""

import os
import pickle
import collections
import networkx as nx

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
OUTP_DIR     = os.path.join(BASE_DIR, "outp")
os.makedirs(OUTP_DIR, exist_ok=True)

GRAPH_PATH   = os.path.join(OUTP_DIR, "global_graph_1992_2002.pkl")
if not os.path.exists(GRAPH_PATH):
    GRAPH_PATH = os.path.join(BASE_DIR, "global_graph_1992_2002.pkl")

METRICS_PATH = os.path.join(OUTP_DIR, "global_node_metrics.pkl")
if not os.path.exists(METRICS_PATH):
    METRICS_PATH = os.path.join(BASE_DIR, "global_node_metrics.pkl")

HTML_OUT     = os.path.join(OUTP_DIR, "global_graph_dashboard.html")
PNG_OUT      = os.path.join(OUTP_DIR, "global_graph_static.png")

print("--> Dang tai do thi va chi so mang...")
with open(GRAPH_PATH, "rb") as f:
    G = pickle.load(f)
with open(METRICS_PATH, "rb") as f:
    metrics = pickle.load(f)

num_nodes = G.number_of_nodes()
num_edges = G.number_of_edges()
print(f"    Loaded: {num_nodes:,} authors, {num_edges:,} edges.")

in_degs   = [m["in_degree"]  for m in metrics.values()]
out_degs  = [m["out_degree"] for m in metrics.values()]
pageranks = [m["pagerank"]   for m in metrics.values()]

# Top 20 authors
top20_cited    = sorted(metrics.items(), key=lambda x: x[1]["in_degree"], reverse=True)[:20]
top20_pagerank = sorted(metrics.items(), key=lambda x: x[1]["pagerank"], reverse=True)[:20]

# ==============================================================================
# 1. TAO DASHBOARD PLOTLY (INTERACTIVE HTML)
# ==============================================================================
print("--> Dang tao Dashboard tuong tac (Plotly)...")

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=(
        "1. So sanh voi Bai bao DeepCas (Table 1)",
        "2. Top 20 Tac gia duoc Trich dan nhieu nhat (In-Degree)",
        "3. Phan phoi In-Degree & Out-Degree (Log-Log Power Law)",
        "4. Top 20 Tac gia theo PageRank toan cuc",
        "5. Tuong quan In-Degree vs PageRank (Top 3,000 tac gia)",
        "6. Mang trich dan cuc bo (Ego-Network) cua Philip S. Yu"
    ),
    vertical_spacing=0.12,
    horizontal_spacing=0.12,
    specs=[
        [{"type": "bar"}, {"type": "bar"}],
        [{"type": "scatter"}, {"type": "bar"}],
        [{"type": "scatter"}, {"type": "scatter"}]
    ]
)

# Panel 1: Bar chart so sanh
fig.add_trace(go.Bar(
    name="Ket qua cua Nhóm",
    x=["So Nut (Authors)", "So Canh (Edges)"],
    y=[num_nodes, num_edges],
    text=[f"{num_nodes:,}", f"{num_edges:,}"],
    textposition="auto",
    marker_color="#1f77b4"
), row=1, col=1)

fig.add_trace(go.Bar(
    name="Target DeepCas (Table 1)",
    x=["So Nut (Authors)", "So Canh (Edges)"],
    y=[131415, 842542],
    text=["131,415 (Khop 98.2%)", "842,542 (Paper refs)"],
    textposition="auto",
    marker_color="#ff7f0e"
), row=1, col=1)

# Panel 2: Top 20 most cited
t20_names = [x[0] for x in top20_cited]
t20_in    = [x[1]["in_degree"] for x in top20_cited]
fig.add_trace(go.Bar(
    x=t20_in[::-1],
    y=t20_names[::-1],
    orientation="h",
    marker_color="#2ca02c",
    hovertemplate="<b>%{y}</b><br>So luot duoc trich dan: %{x:,}<extra></extra>"
), row=1, col=2)

# Panel 3: Degree distribution (Log-log)
indeg_counts = collections.Counter(in_degs)
in_x = sorted(indeg_counts.keys())
in_y = [indeg_counts[k] for k in in_x]

outdeg_counts = collections.Counter(out_degs)
out_x = sorted(outdeg_counts.keys())
out_y = [outdeg_counts[k] for k in out_x]

fig.add_trace(go.Scatter(
    x=in_x, y=in_y,
    mode="markers",
    name="In-Degree",
    marker=dict(size=5, color="#1f77b4", opacity=0.7),
    hovertemplate="In-degree %{x}: %{y:,} tac gia<extra></extra>"
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=out_x, y=out_y,
    mode="markers",
    name="Out-Degree",
    marker=dict(size=5, color="#d62728", opacity=0.7),
    hovertemplate="Out-degree %{x}: %{y:,} tac gia<extra></extra>"
), row=2, col=1)

# Panel 4: Top 20 PageRank
pr_names = [x[0] for x in top20_pagerank]
pr_vals  = [x[1]["pagerank"] for x in top20_pagerank]
fig.add_trace(go.Bar(
    x=pr_vals[::-1],
    y=pr_names[::-1],
    orientation="h",
    marker_color="#9467bd",
    hovertemplate="<b>%{y}</b><br>PageRank: %{x:.6f}<extra></extra>"
), row=2, col=2)

# Panel 5: Scatter In-Degree vs PageRank
top3k = sorted(metrics.items(), key=lambda x: x[1]["in_degree"], reverse=True)[:3000]
sc_x = [x[1]["in_degree"] for x in top3k]
sc_y = [x[1]["pagerank"] for x in top3k]
sc_names = [x[0] for x in top3k]

fig.add_trace(go.Scatter(
    x=sc_x, y=sc_y,
    mode="markers",
    marker=dict(size=6, color=sc_y, colorscale="Viridis", opacity=0.7),
    text=sc_names,
    hovertemplate="<b>%{text}</b><br>In-degree: %{x:,}<br>PageRank: %{y:.6f}<extra></extra>"
), row=3, col=1)

# Panel 6: Ego-network of Philip S. Yu (Top author)
root_author = "Philip S. Yu"
# Get top 25 neighbors connected to Philip S. Yu
in_nbrs  = sorted(G.predecessors(root_author), key=lambda x: metrics[x]["in_degree"], reverse=True)[:15]
out_nbrs = sorted(G.successors(root_author),   key=lambda x: metrics[x]["in_degree"], reverse=True)[:15]
sub_nodes = list(set([root_author] + in_nbrs + out_nbrs))
subG = G.subgraph(sub_nodes)

pos = nx.spring_layout(subG, seed=42, k=0.5)

edge_x = []
edge_y = []
for u, v in subG.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

fig.add_trace(go.Scatter(
    x=edge_x, y=edge_y,
    mode="lines",
    line=dict(width=1, color="#bdbdbd"),
    hoverinfo="none",
    showlegend=False
), row=3, col=2)

node_x = [pos[n][0] for n in subG.nodes()]
node_y = [pos[n][1] for n in subG.nodes()]
node_colors = ["#d62728" if n == root_author else "#1f77b4" for n in subG.nodes()]
node_sizes  = [20 if n == root_author else 10 for n in subG.nodes()]
node_text   = [f"{n}<br>In-degree: {metrics[n]['in_degree']}" for n in subG.nodes()]

fig.add_trace(go.Scatter(
    x=node_x, y=node_y,
    mode="markers+text",
    marker=dict(size=node_sizes, color=node_colors),
    text=[n.split()[-1] for n in subG.nodes()],  # show last name on plot
    textposition="top center",
    hovertext=node_text,
    hoverinfo="text",
    showlegend=False
), row=3, col=2)

# Axis configurations
fig.update_xaxes(type="log", title_text="So luong", row=1, col=1)
fig.update_xaxes(title_text="So luong trich dan (In-Degree)", row=1, col=2)
fig.update_xaxes(type="log", title_text="Bậc (Degree)", row=2, col=1)
fig.update_yaxes(type="log", title_text="So luong tac gia", row=2, col=1)
fig.update_xaxes(title_text="Chi so PageRank", row=2, col=2)
fig.update_xaxes(type="log", title_text="In-Degree (Log scale)", row=3, col=1)
fig.update_yaxes(type="log", title_text="PageRank (Log scale)", row=3, col=1)
fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=3, col=2)
fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=3, col=2)

fig.update_layout(
    title=dict(
        text="<b>Task A: Mạng Trích Dẫn Tác Giả Toàn Cục G (1992–2002) - Chuẩn DeepCas</b><br>"
             f"<sup>Tong: {num_nodes:,} Tac gia (98.2% khop voi 131,415) | {num_edges:,} Canh quan he trich dan</sup>",
        x=0.5
    ),
    height=1200,
    template="plotly_white",
    font=dict(family="Segoe UI, Arial", size=11),
    showlegend=True
)

fig.write_html(HTML_OUT, include_plotlyjs=True)
print(f"==> Da luu Dashboard tuong tac -> {HTML_OUT}")


# ==============================================================================
# 2. TAO ANH TINH MATPLOTLIB (STATIC PNG CHO BAO CAO)
# ==============================================================================
print("--> Dang tao anh tinh PNG (Matplotlib)...")
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig2, axes = plt.subplots(3, 2, figsize=(16, 18))
fig2.suptitle(
    f"Task A: Author Citation Network G (1992–2002)\n"
    f"{num_nodes:,} Authors (vs target 131,415) | {num_edges:,} Citation Edges",
    fontsize=15, fontweight="bold", y=0.98
)

# 1. So sanh voi DeepCas
ax = axes[0, 0]
categories = ["Nodes (Authors)", "Edges"]
our_vals = [num_nodes, num_edges]
paper_vals = [131415, 842542]
x_pos = [0, 1]
width = 0.35
ax.bar([p - width/2 for p in x_pos], our_vals, width=width, label="Nhom minh", color="#1f77b4")
ax.bar([p + width/2 for p in x_pos], paper_vals, width=width, label="DeepCas Target", color="#ff7f0e")
ax.set_xticks(x_pos)
ax.set_xticklabels(categories, fontweight="bold")
ax.set_yscale("log")
ax.set_ylabel("So luong (Log scale)")
ax.set_title("1. So sanh truc dien voi DeepCas Table 1", fontweight="bold")
ax.legend()
for i, (v1, v2) in enumerate(zip(our_vals, paper_vals)):
    ax.text(i - width/2, v1 * 1.15, f"{v1:,}", ha="center", fontsize=8)
    ax.text(i + width/2, v2 * 1.15, f"{v2:,}", ha="center", fontsize=8)

# 2. Top 15 most cited authors
ax = axes[0, 1]
top15 = top20_cited[:15]
t15_names = [x[0] for x in top15]
t15_vals  = [x[1]["in_degree"] for x in top15]
ax.barh(range(len(top15)), t15_vals[::-1], color="#2ca02c")
ax.set_yticks(range(len(top15)))
ax.set_yticklabels(t15_names[::-1], fontsize=9)
ax.set_xlabel("So luot duoc trich dan (In-Degree)")
ax.set_title("2. Top 15 Tac gia duoc trich dan nhieu nhat", fontweight="bold")

# 3. Degree distribution (Log-log)
ax = axes[1, 0]
ax.scatter(in_x, in_y, s=10, color="#1f77b4", alpha=0.7, label="In-Degree")
ax.scatter(out_x, out_y, s=10, color="#d62728", alpha=0.5, label="Out-Degree")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Bậc (Degree)")
ax.set_ylabel("So luong tac gia")
ax.set_title("3. Phan phoi Bac In-Degree va Out-Degree (Power Law)", fontweight="bold")
ax.legend()

# 4. Top 15 PageRank
ax = axes[1, 1]
top15_pr = top20_pagerank[:15]
pr15_names = [x[0] for x in top15_pr]
pr15_vals  = [x[1]["pagerank"] for x in top15_pr]
ax.barh(range(len(top15_pr)), pr15_vals[::-1], color="#9467bd")
ax.set_yticks(range(len(top15_pr)))
ax.set_yticklabels(pr15_names[::-1], fontsize=9)
ax.set_xlabel("PageRank")
ax.set_title("4. Top 15 Tac gia theo chi so PageRank", fontweight="bold")

# 5. Scatter In-Degree vs PageRank
ax = axes[2, 0]
sc = ax.scatter(sc_x, sc_y, s=8, c=sc_y, cmap="viridis", alpha=0.6)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("In-Degree (Log scale)")
ax.set_ylabel("PageRank (Log scale)")
ax.set_title("5. Tuong quan In-Degree vs PageRank (Top 3,000 tac gia)", fontweight="bold")
cbar = fig2.colorbar(sc, ax=ax, shrink=0.8)
cbar.set_label("PageRank")

# 6. Ego-network of Philip S. Yu
ax = axes[2, 1]
nx.draw_networkx_edges(subG, pos, ax=ax, edge_color="#bdbdbd", alpha=0.5, arrows=True, arrowsize=8)
colors = ["#d62728" if n == root_author else "#1f77b4" for n in subG.nodes()]
sizes  = [300 if n == root_author else 80 for n in subG.nodes()]
nx.draw_networkx_nodes(subG, pos, ax=ax, node_color=colors, node_size=sizes)
labels = {n: n.split()[-1] for n in subG.nodes()}
nx.draw_networkx_labels(subG, pos, labels, ax=ax, font_size=8)
ax.set_title(f"6. Mang trich dan cuc bo quanh '{root_author}'", fontweight="bold")
ax.axis("off")

plt.tight_layout(rect=[0, 0, 1, 0.97])
fig2.savefig(PNG_OUT, dpi=180, bbox_inches="tight")
plt.close(fig2)
print(f"==> Da luu anh tinh PNG -> {PNG_OUT}")
print("Hoan thanh visualization!")
