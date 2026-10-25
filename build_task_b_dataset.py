"""Task B: build cascade dataset from the Task A global graph.

This script supports two modes:
1) Real mode: reads the AMiner raw DBLP file and the Task A graph pickle, then
   builds one-year cascades for papers from 2003-2009.
2) Demo mode: if the graph/raw data are not available, creates a tiny synthetic
   dataset so the team can still test the output format.

Expected outputs:
- outp/task_b/train.csv
- outp/task_b/val.csv
- outp/task_b/test.csv
- outp/task_b/cascade_growth_distribution.png
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "outp" / "task_b"
DEFAULT_GRAPH_PATH = BASE_DIR / "outp" / "global_graph_1992_2002.pkl"
DEFAULT_RAW_DBLP_PATH = BASE_DIR / "dblp.v8" / "dblp.txt"


def normalize_authors(raw: object) -> List[str]:
    if raw is None or pd.isna(raw):
        return []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        if "|" in raw:
            items = raw.split("|")
        else:
            items = raw.split(",")
    else:
        items = [str(raw)]
    return [str(item).strip() for item in items if str(item).strip()]


def parse_dblp_blocks(input_file: Path, year_min: int = 2003, year_max: int = 2009) -> Dict[str, Dict[str, object]]:
    """Stream-parse raw DBLP and keep only papers in the Task B year range.

    This keeps memory usage manageable because Task B only needs papers published in
    2003-2009; we do not store every paper in the full DBLP dump.
    """
    if not input_file.exists():
        return {}

    papers: Dict[str, Dict[str, object]] = {}
    current: Dict[str, object] = {}
    refs: List[str] = []

    with open(input_file, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            if line == "":
                pid = str(current.get("index", "")).strip()
                year = current.get("year")
                authors = current.get("authors", [])
                if pid and year is not None:
                    year_int = int(year)
                    if year_min <= year_int <= year_max:
                        papers[pid] = {
                            "paper_id": pid,
                            "year": year_int,
                            "authors": list(authors),
                            "references": refs[:],
                        }
                current = {}
                refs = []
                continue

            if line.startswith("#index"):
                current["index"] = line[6:].strip()
            elif line.startswith("#t"):
                try:
                    current["year"] = int(line[2:].strip())
                except ValueError:
                    current["year"] = None
            elif line.startswith("#@"):
                current["authors"] = normalize_authors(line[2:])
            elif line.startswith("#%"):
                ref_id = line[2:].strip()
                if ref_id:
                    refs.append(ref_id)

    pid = str(current.get("index", "")).strip()
    year = current.get("year")
    authors = current.get("authors", [])
    if pid and year is not None:
        year_int = int(year)
        if year_min <= year_int <= year_max:
            papers[pid] = {
                "paper_id": pid,
                "year": year_int,
                "authors": list(authors),
                "references": refs[:],
            }

    return papers


def load_graph(graph_path: Path):
    if not graph_path.exists():
        return None
    try:
        import pickle
        with open(graph_path, "rb") as fh:
            return pickle.load(fh)
    except Exception:
        return None


def generate_demo_papers(num_papers: int = 120, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    author_pool = [
        "Alice Chen", "Bob Kumar", "Carla Santos", "David Nguyen", "Eva Rossi",
        "Frank Lin", "Grace Park", "Hank Miller", "Iris Gomez", "Jack Turner",
        "Khan Ali", "Laura Becker", "Ming Zhou", "Nina Patel", "Oscar Silva",
        "Priya Nair", "Quentin Brooks", "Rita Flores", "Sam Lee", "Tara Wilson",
    ]

    papers: List[Dict[str, object]] = []
    paper_counter = 0
    for year in range(2003, 2010):
        yearly_count = max(12, num_papers // 7)
        for _ in range(yearly_count):
            paper_counter += 1
            pid = f"P_{year}_{paper_counter:03d}"
            author_count = rng.randint(2, 4)
            authors = rng.sample(author_pool, author_count)
            refs: List[str] = []
            prior = [p for p in papers if p["year"] < year]
            if prior:
                ref_count = rng.randint(0, min(3, len(prior)))
                refs = [rng.choice(prior)["paper_id"] for _ in range(ref_count)]
            papers.append({
                "paper_id": pid,
                "year": year,
                "authors": "|".join(authors),
                "references": "|".join(refs),
            })

    return pd.DataFrame(papers)[["paper_id", "year", "authors", "references"]]


def build_cascade_for_paper(
    paper_row: pd.Series,
    paper_lookup: Optional[Dict[str, pd.Series]] = None,
    graph=None,
    next_year_citing_rows: Optional[Dict[str, List[pd.Series]]] = None,
) -> Dict[str, object]:
    paper_id = str(paper_row["paper_id"])
    year = int(paper_row["year"])
    root_authors = set(normalize_authors(paper_row.get("authors", "")))

    citing_authors: Set[str] = set()
    if next_year_citing_rows is not None:
        for candidate_row in next_year_citing_rows.get(paper_id, []):
            if int(candidate_row["year"]) != year + 1:
                continue
            citing_authors.update(normalize_authors(candidate_row.get("authors", "")))
    elif paper_lookup is not None:
        for candidate_row in paper_lookup.values():
            if int(candidate_row["year"]) != year + 1:
                continue
            cited_ids = set(normalize_authors(candidate_row.get("references", "")))
            if paper_id in cited_ids:
                citing_authors.update(normalize_authors(candidate_row.get("authors", "")))

    if graph is not None:
        try:
            valid_nodes = set(graph.nodes())
            root_authors = {a for a in root_authors if a in valid_nodes}
            citing_authors = {a for a in citing_authors if a in valid_nodes}
        except Exception:
            pass

    cascade_authors = root_authors | citing_authors
    delta_s = max(0, len(cascade_authors) - len(root_authors))
    label_y = math.log2(delta_s + 1.0)

    return {
        "paper_id": paper_id,
        "year": year,
        "cascade_size": len(cascade_authors),
        "delta_s": delta_s,
        "y": label_y,
    }


def balance_zero_growth(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    zero_mask = df["delta_s"] == 0
    zero_idx = df.index[zero_mask].tolist()
    if len(zero_idx) <= 1:
        return df

    drop_count = max(1, len(zero_idx) // 2)
    rng = random.Random(seed)
    drop_idx = rng.sample(zero_idx, drop_count)
    return df.drop(index=drop_idx)


def build_dataset_from_raw(raw_path: Path, graph_path: Path, output_dir: Path) -> pd.DataFrame:
    graph = load_graph(graph_path)
    raw_papers = parse_dblp_blocks(raw_path, year_min=2003, year_max=2009)
    valid_rows = []
    for paper in raw_papers.values():
        year = paper.get("year")
        if year is None or not (2003 <= year <= 2009):
            continue
        valid_rows.append({
            "paper_id": paper["paper_id"],
            "year": year,
            "authors": "|".join(paper["authors"]),
            "references": "|".join(paper["references"]),
        })

    paper_df = pd.DataFrame(valid_rows)
    if paper_df.empty:
        raise ValueError(f"No papers found in {raw_path} for 2003-2009")

    paper_lookup = {
        str(row["paper_id"]): row
        for _, row in paper_df.iterrows()
        if str(row.get("paper_id", "")).strip()
    }

    next_year_citing_rows: Dict[str, List[pd.Series]] = {}
    for _, row in paper_df.iterrows():
        ref_list = normalize_authors(row.get("references", ""))
        for ref_id in ref_list:
            next_year_citing_rows.setdefault(ref_id, []).append(row)

    cascade_rows = []
    for _, row in paper_df.iterrows():
        cascade_rows.append(
            build_cascade_for_paper(
                row,
                paper_lookup=paper_lookup,
                graph=graph,
                next_year_citing_rows=next_year_citing_rows,
            )
        )

    cascade_df = pd.DataFrame(cascade_rows)
    cascade_df = balance_zero_growth(cascade_df)
    cascade_df["split"] = "train"
    cascade_df.loc[cascade_df["year"] == 2008, "split"] = "val"
    cascade_df.loc[cascade_df["year"] == 2009, "split"] = "test"

    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ["train", "val", "test"]:
        split_df = cascade_df[cascade_df["split"] == split_name].copy()
        split_df = split_df[["paper_id", "year", "cascade_size", "delta_s", "y", "split"]]
        split_df.to_csv(output_dir / f"{split_name}.csv", index=False)

    return cascade_df


def build_dataset_from_demo(output_dir: Path, num_papers: int = 120) -> pd.DataFrame:
    demo_df = generate_demo_papers(num_papers=num_papers)
    paper_lookup = {
        str(row["paper_id"]): row
        for _, row in demo_df.iterrows()
        if str(row.get("paper_id", "")).strip()
    }
    cascade_rows = [build_cascade_for_paper(row, paper_lookup) for _, row in demo_df.iterrows()]
    cascade_df = pd.DataFrame(cascade_rows)
    cascade_df = balance_zero_growth(cascade_df)
    cascade_df["split"] = "train"
    cascade_df.loc[cascade_df["year"] == 2008, "split"] = "val"
    cascade_df.loc[cascade_df["year"] == 2009, "split"] = "test"

    output_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ["train", "val", "test"]:
        split_df = cascade_df[cascade_df["split"] == split_name].copy()
        split_df = split_df[["paper_id", "year", "cascade_size", "delta_s", "y", "split"]]
        split_df.to_csv(output_dir / f"{split_name}.csv", index=False)

    return cascade_df


def plot_distribution(cascade_df: pd.DataFrame, output_path: Path) -> None:
    if plt is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].hist(cascade_df["delta_s"], bins=30, color="#4C72B0", edgecolor="black")
    axes[0].set_title("Distribution of delta_s")
    axes[0].set_xlabel("Delta_s")
    axes[0].set_ylabel("Count")

    axes[1].hist(cascade_df["y"], bins=30, color="#55A868", edgecolor="black")
    axes[1].set_title("Distribution of y = log2(delta_s + 1)")
    axes[1].set_xlabel("y")
    axes[1].set_ylabel("Count")

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task B cascade dataset from the real Task A graph or a demo fallback.")
    parser.add_argument("--graph", type=str, default=str(DEFAULT_GRAPH_PATH), help="Path to the Task A graph pickle")
    parser.add_argument("--raw-dblp", type=str, default=str(DEFAULT_RAW_DBLP_PATH), help="Path to the raw AMiner DBLP file")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Directory for train/val/test outputs")
    parser.add_argument("--demo", action="store_true", help="Force demo fallback even if the real graph/data exist")
    parser.add_argument("--num-papers", type=int, default=120, help="Demo dataset size if fallback is used")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    graph_path = Path(args.graph)
    raw_path = Path(args.raw_dblp)

    if args.demo or (not graph_path.exists() and not raw_path.exists()):
        cascade_df = build_dataset_from_demo(output_dir, num_papers=args.num_papers)
        print("Using demo fallback mode.")
    elif graph_path.exists() and raw_path.exists():
        cascade_df = build_dataset_from_raw(raw_path, graph_path, output_dir)
        print("Using real Task A graph + raw DBLP data.")
    elif raw_path.exists():
        cascade_df = build_dataset_from_raw(raw_path, graph_path, output_dir)
        print("Using raw DBLP data with Task A graph if available.")
    else:
        cascade_df = build_dataset_from_demo(output_dir, num_papers=args.num_papers)
        print("No real dataset found; using demo fallback.")

    try:
        plot_distribution(cascade_df, output_dir / "cascade_growth_distribution.png")
        plot_status = str(output_dir / "cascade_growth_distribution.png")
    except Exception as exc:
        plot_status = f"skipped ({exc})"

    train_count = int((cascade_df["split"] == "train").sum())
    val_count = int((cascade_df["split"] == "val").sum())
    test_count = int((cascade_df["split"] == "test").sum())

    print(f"Train: {train_count}")
    print(f"Val:   {val_count}")
    print(f"Test:  {test_count}")
    print(f"Output dir: {output_dir}")
    print(f"Plot: {plot_status}")


if __name__ == "__main__":
    main()
