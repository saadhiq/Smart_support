"""Explore the Bitext dataset and write ml/reports/explore.md."""

import re
import string
from pathlib import Path

import pandas as pd
from datasets import load_dataset

DATASET_ID = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
REPORT_PATH = Path(__file__).parent / "reports" / "explore.md"
PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}")
PUNCT_TABLE = str.maketrans("", "", string.punctuation)
SEED = 42


def load_frame() -> pd.DataFrame:
    """Download the dataset from Hugging Face and return it as a DataFrame."""
    return load_dataset(DATASET_ID, split="train").to_pandas()


def explore_normalise(text: str) -> str:
    """Lowercase, replace {{...}} with ENT, strip punctuation, collapse spaces."""
    text = PLACEHOLDER_RE.sub(" ENT ", text.lower())
    text = text.translate(PUNCT_TABLE)
    return " ".join(text.split())


def md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a Markdown table without extra dependencies."""
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = [str(v).replace("|", "\\|").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def section_overview(df: pd.DataFrame) -> str:
    """Row count and columns."""
    return f"## 1. Overview\n\nRows: **{len(df):,}**\n\nColumns: {', '.join(df.columns)}\n"


def section_labels(df: pd.DataFrame) -> str:
    """Counts per category and intent, and which intents belong to each category."""
    cat = df["category"].value_counts().rename_axis("category").reset_index(name="rows")
    cat["share_%"] = (cat["rows"] / len(df) * 100).round(1)
    intent = df["intent"].value_counts().rename_axis("intent").reset_index(name="rows")
    mapping = (
        df.groupby("category")["intent"].agg(lambda s: ", ".join(sorted(s.unique())))
        .reset_index(name="intents")
    )
    per_intent_cats = df.groupby("intent")["category"].nunique()
    multi = per_intent_cats[per_intent_cats > 1]
    note = (
        "Every intent belongs to exactly one category."
        if multi.empty
        else f"Intents with more than one category: {', '.join(multi.index)}"
    )
    return (
        f"## 2. Labels\n\n{df['category'].nunique()} categories, "
        f"{df['intent'].nunique()} intents.\n\n### Rows per category\n\n{md_table(cat)}\n\n"
        f"### Rows per intent\n\n{md_table(intent)}\n\n"
        f"### Intents in each category\n\n{md_table(mapping)}\n\n{note}\n"
    )


def section_lengths(df: pd.DataFrame) -> str:
    """Message length in words: min, median, max, overall and per category."""
    words = df["instruction"].str.split().str.len()
    per_cat = (
        words.groupby(df["category"]).agg(["min", "median", "max"]).reset_index()
    )
    return (
        f"## 3. Message length (words)\n\nmin {words.min()}, median {words.median():.0f}, "
        f"max {words.max()}\n\n{md_table(per_cat)}\n"
    )


def section_examples(df: pd.DataFrame) -> str:
    """Three random examples per category."""
    parts = ["## 4. Examples (3 per category, random_state=42)\n"]
    for category, group in df.groupby("category"):
        sample = group.sample(n=min(3, len(group)), random_state=SEED)
        parts.append(f"### {category}\n\n{md_table(sample[['intent', 'instruction']])}\n")
    return "\n".join(parts)


def section_duplicates(df: pd.DataFrame) -> str:
    """Exact duplicates and duplicates after normalisation."""
    exact = int(df["instruction"].duplicated().sum())
    norm = df["instruction"].map(explore_normalise)
    after = int(norm.duplicated().sum())
    top = norm.value_counts().head(10).rename_axis("normalised instruction").reset_index(name="times")
    return (
        "## 5. Duplicates\n\n"
        f"Exact duplicate instructions (extra copies): **{exact:,}** "
        f"({exact / len(df) * 100:.1f}%)\n\n"
        f"Duplicates after normalising (lowercase, no punctuation, {{{{...}}}} -> ENT): "
        f"**{after:,}** ({after / len(df) * 100:.1f}%). Unique normalised texts: "
        f"{norm.nunique():,}\n\n### Most repeated normalised texts\n\n{md_table(top)}\n"
    )


def section_conflicts(df: pd.DataFrame) -> str:
    """Normalised instructions that appear with more than one category."""
    norm = df.assign(norm=df["instruction"].map(explore_normalise))
    cats = norm.groupby("norm")["category"].agg(lambda s: sorted(s.unique()))
    conflicts = cats[cats.map(len) > 1]
    rows = norm[norm["norm"].isin(conflicts.index)]
    pairs = conflicts.map(" / ".join).value_counts().rename_axis("categories").reset_index(name="texts")
    examples = (
        rows.groupby("norm")
        .agg(categories=("category", lambda s: " / ".join(sorted(s.unique()))),
             intents=("intent", lambda s: " / ".join(sorted(s.unique()))),
             rows=("category", "size"))
        .reset_index()
        .head(15)
    )
    return (
        "## 6. Same text, different category\n\n"
        f"Normalised texts with more than one category: **{len(conflicts):,}**, "
        f"covering **{len(rows):,}** rows.\n\n"
        + (f"### Category combinations\n\n{md_table(pairs)}\n\n"
           f"### Examples\n\n{md_table(examples)}\n" if len(conflicts) else "")
    )


def section_placeholders(df: pd.DataFrame) -> str:
    """Rows with {{...}} placeholders and the 15 most common ones."""
    found = df["instruction"].str.findall(PLACEHOLDER_RE)
    has = int((found.str.len() > 0).sum())
    top = found.explode().dropna().value_counts().head(15)
    top = top.rename_axis("placeholder").reset_index(name="count")
    return (
        "## 7. Placeholders\n\n"
        f"Rows containing a {{{{...}}}} placeholder: **{has:,}** ({has / len(df) * 100:.1f}%)\n\n"
        f"{md_table(top)}\n"
    )


def section_flags(df: pd.DataFrame) -> str:
    """Value counts of the flags column (top 20)."""
    counts = df["flags"].value_counts()
    top = counts.head(20).rename_axis("flags").reset_index(name="rows")
    return (
        f"## 8. Flags\n\n{counts.size} distinct flag combinations. Top 20:\n\n{md_table(top)}\n\n"
        "Flag letters per the dataset card: B basic syntax, I interrogative, "
        "C coordinated, N negation, M morphological variation, L semantic variation "
        "(synonyms), P politeness, Q colloquial, W offensive, K keyword mode, "
        "E abbreviations, Z errors and typos.\n"
    )


def section_shortcuts(df: pd.DataFrame) -> str:
    """Placeholders and digits that reveal the category on their own."""
    ph = df.assign(p=df["instruction"].str.findall(PLACEHOLDER_RE)).explode("p").dropna(subset=["p"])
    purity = (
        ph.groupby("p")["category"]
        .agg(rows="size", top_category=lambda s: s.value_counts().index[0],
             share_in_top=lambda s: round(s.value_counts(normalize=True).iloc[0], 2))
        .reset_index().rename(columns={"p": "placeholder"})
        .sort_values("rows", ascending=False)
    )
    digits = df[df["instruction"].str.contains(r"\d")]["category"].value_counts()
    digits = digits.rename_axis("category").reset_index(name="rows_with_digits")
    return (
        "## 9. Shortcut clues (placeholders and digits)\n\n"
        "If a token only ever appears with one category, a model can learn the token "
        "instead of the meaning. Real customers never type {{...}}.\n\n"
        f"{md_table(purity)}\n\n### Rows containing digits\n\n{md_table(digits)}\n"
    )


def main() -> None:
    """Build the exploration report."""
    df = load_frame()
    sections = [
        section_overview, section_labels, section_lengths, section_examples,
        section_duplicates, section_conflicts, section_placeholders, section_flags, section_shortcuts,
    ]
    report = "# Bitext dataset exploration\n\n" + "\n".join(f(df) for f in sections)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"rows={len(df)} categories={df['category'].nunique()} -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
