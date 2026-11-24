"""Clean the Bitext data and make a leak-free grouped train/test split."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.neighbors import NearestNeighbors

from app.text import normalise
from ml.explore import load_frame, md_table

ML_DIR = Path(__file__).parent
DATA_DIR = ML_DIR / "data"
REPORT_PATH = ML_DIR / "reports" / "split.md"
SIM_THRESHOLD = 0.85
COMPARE_THRESHOLDS = (0.9, 0.85, 0.8)
N_FOLDS = 5  # one fold of five = 20% test
TEST_SIZE = 0.2
SEED = 42


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Drop exact duplicates after normalise() and texts with conflicting categories."""
    df = df.assign(norm=df["instruction"].map(normalise))
    n_cats = df.groupby("norm")["category"].transform("nunique")
    conflicts = df[n_cats > 1]
    df = df[n_cats == 1]
    before = len(df)
    df = df.drop_duplicates(subset="norm", keep="first").reset_index(drop=True)
    stats = {
        "rows_loaded": before + len(conflicts),
        "conflict_rows_dropped": len(conflicts),
        "conflict_texts": conflicts["norm"].nunique(),
        "duplicate_rows_dropped": before - len(df),
        "rows_kept": len(df),
    }
    return df, stats


def char_vectors(texts: pd.Series) -> TfidfVectorizer:
    """Fit a character 3-5-gram TF-IDF vectoriser for similarity measurement."""
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit(texts)


def near_duplicate_groups(texts: pd.Series, threshold: float) -> np.ndarray:
    """Group texts linked by cosine similarity >= threshold (connected components)."""
    x = char_vectors(texts).transform(texts)
    nn = NearestNeighbors(radius=1 - threshold, metric="cosine", algorithm="brute").fit(x)
    neighbours = nn.radius_neighbors(x, return_distance=False)
    rows = np.repeat(np.arange(len(neighbours)), [len(n) for n in neighbours])
    cols = np.concatenate(neighbours)
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(texts), len(texts)))
    _, labels = connected_components(graph, directed=False)
    return labels


def group_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by group_id (whole families on one side), keeping category shares similar."""
    sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    train_idx, test_idx = next(sgkf.split(df, df["category"], groups=df["group_id"]))
    return df.iloc[train_idx], df.iloc[test_idx]


def threshold_row(df: pd.DataFrame, threshold: float, vec: TfidfVectorizer) -> dict[str, str]:
    """Group and split at one threshold; summarise group sizes, balance and leakage."""
    trial = df.assign(group_id=near_duplicate_groups(df["norm"], threshold))
    train, test = group_split(trial)
    sizes = trial["group_id"].value_counts()
    gap = (test["category"].value_counts(normalize=True)
           - train["category"].value_counts(normalize=True)).abs().max()
    sims = max_similarity_to_train(train["norm"], test["norm"], vec)
    return {
        "threshold": f"{threshold}" + (" (used)" if threshold == SIM_THRESHOLD else ""),
        "groups": f"{len(sizes):,}",
        "largest group": f"{sizes.max():,} ({sizes.max() / len(trial) * 100:.1f}%)",
        "test share": f"{len(test) / len(trial) * 100:.1f}%",
        "max category gap": f"{gap * 100:.1f} pts",
        "test sim >= 0.8": f"{(sims >= 0.8).mean() * 100:.1f}%",
    }


def max_similarity_to_train(train: pd.Series, test: pd.Series, vec: TfidfVectorizer) -> np.ndarray:
    """For each test text, cosine similarity to its closest training text."""
    nn = NearestNeighbors(n_neighbors=1, metric="cosine", algorithm="brute")
    nn.fit(vec.transform(train))
    dist, _ = nn.kneighbors(vec.transform(test))
    return 1 - dist[:, 0]


def leak_row(name: str, sims: np.ndarray) -> dict[str, str]:
    """Summarise a similarity array as a report row."""
    return {
        "split": name,
        "test rows": f"{len(sims):,}",
        "sim >= 0.9": f"{(sims >= 0.9).mean() * 100:.1f}%",
        "sim >= 0.8": f"{(sims >= 0.8).mean() * 100:.1f}%",
        "median sim": f"{np.median(sims):.2f}",
    }


def group_table(df: pd.DataFrame) -> pd.DataFrame:
    """The 10 largest near-duplicate groups with size, categories and an example."""
    g = df.groupby("group_id").agg(
        rows=("norm", "size"),
        categories=("category", lambda s: " / ".join(sorted(s.unique()))),
        example=("norm", "first"),
    )
    return g.sort_values("rows", ascending=False).head(10).reset_index()


def category_table(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Category counts and shares in train and test."""
    t = pd.DataFrame({"train": train["category"].value_counts(),
                      "test": test["category"].value_counts()}).fillna(0).astype(int)
    t["train_%"] = (t["train"] / t["train"].sum() * 100).round(1)
    t["test_%"] = (t["test"] / t["test"].sum() * 100).round(1)
    return t.rename_axis("category").reset_index()


def write_report(stats: dict[str, int], df: pd.DataFrame, train: pd.DataFrame,
                 test: pd.DataFrame, leaks: list[dict[str, str]],
                 thresholds: list[dict[str, str]]) -> None:
    """Write ml/reports/split.md."""
    sizes = df["group_id"].value_counts()
    mixed = df.groupby("group_id")["category"].nunique()
    mixed_ids = mixed[mixed > 1].index
    mixed_rows = df[df["group_id"].isin(mixed_ids)]
    mixed_examples = (
        mixed_rows.groupby("group_id")
        .apply(lambda g: g.drop_duplicates("category").head(3)[["category", "norm"]],
               include_groups=False)
        .reset_index(level=0).head(15)
    )
    report = f"""# Cleaning and leak-free split

## Cleaning (text compared after app.text.normalise)

| step | rows |
|---|---|
| loaded | {stats['rows_loaded']:,} |
| dropped: same text with more than one category ({stats['conflict_texts']} texts) | {stats['conflict_rows_dropped']:,} |
| dropped: exact duplicates after normalise | {stats['duplicate_rows_dropped']:,} |
| kept | {stats['rows_kept']:,} |

## Near-duplicate groups

Character 3-5-gram TF-IDF on the normalised text. Two texts are linked when cosine
similarity >= {SIM_THRESHOLD}. Linked texts form one group (connected components).

- Groups: **{df['group_id'].nunique():,}** for {len(df):,} rows
- Single-row groups: {(sizes == 1).sum():,}
- Largest group: {sizes.max():,} rows ({sizes.max() / len(df) * 100:.1f}% of all rows)
- Groups containing more than one category: **{len(mixed_ids)}** ({len(mixed_rows):,} rows)

### 10 largest groups

{md_table(group_table(df))}

### Near-identical texts with different categories (possible doubtful labels)

{md_table(mixed_examples) if len(mixed_ids) else "None."}

### Choosing the threshold

A lower threshold makes groups bigger, so the test set is less similar to train
(stricter). Too low, and groups chain together into huge mixed groups and the
category balance breaks.

{md_table(pd.DataFrame(thresholds))}

## Split

StratifiedGroupKFold(n_splits={N_FOLDS}, shuffle=True, random_state={SEED}); the first
fold is the test set. Whole groups go to one side; category shares are kept similar.
Train {len(train):,} rows, test {len(test):,} rows ({len(test) / len(df) * 100:.1f}%).
No group_id appears in both: {set(train['group_id']).isdisjoint(test['group_id'])}.

{md_table(category_table(train, test))}

## Leak check

For every test row: cosine similarity to its closest training row (same character
TF-IDF). The random split is shown only for comparison; it is not used.

{md_table(pd.DataFrame(leaks))}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    """Clean, group, split, check for leaks, save parquet files and the report."""
    df, stats = clean(load_frame())
    vec = char_vectors(df["norm"])
    thresholds = [threshold_row(df, t, vec) for t in COMPARE_THRESHOLDS]
    df["group_id"] = near_duplicate_groups(df["norm"], SIM_THRESHOLD)
    train, test = group_split(df)
    rand_train, rand_test = train_test_split(df, test_size=TEST_SIZE, random_state=SEED)
    leaks = [
        leak_row("grouped (used)", max_similarity_to_train(train["norm"], test["norm"], vec)),
        leak_row("random (comparison only)",
                 max_similarity_to_train(rand_train["norm"], rand_test["norm"], vec)),
    ]
    DATA_DIR.mkdir(exist_ok=True)
    cols = ["instruction", "norm", "category", "intent", "flags", "group_id"]
    train[cols].to_parquet(DATA_DIR / "train.parquet", index=False)
    test[cols].to_parquet(DATA_DIR / "test.parquet", index=False)
    write_report(stats, df, train, test, leaks, thresholds)
    print(f"kept={len(df)} groups={df['group_id'].nunique()} train={len(train)} "
          f"test={len(test)} -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
