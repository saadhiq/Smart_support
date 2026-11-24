"""Train the TF-IDF and LogisticRegression category classifier."""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline

from app.text import normalise
from ml.explore import md_table
from ml.prepare import char_vectors, max_similarity_to_train

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "ml" / "data"
MODEL_PATH = ROOT / "models" / "classifier.joblib"
META_PATH = ROOT / "models" / "classifier_meta.json"
REPORT_PATH = ROOT / "ml" / "reports" / "model.md"
C_GRID = [0.5, 1, 2, 5]
N_FOLDS = 5


def build_pipeline() -> Pipeline:
    """normalise() -> word 1-2-grams + char_wb 3-5-grams TF-IDF -> logistic regression."""
    features = FeatureUnion([
        ("word", TfidfVectorizer(preprocessor=normalise, analyzer="word",
                                 ngram_range=(1, 2), sublinear_tf=True)),
        ("char", TfidfVectorizer(preprocessor=normalise, analyzer="char_wb",
                                 ngram_range=(3, 5), sublinear_tf=True)),
    ])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    return Pipeline([("features", features), ("clf", clf)])


def tune(train: pd.DataFrame) -> GridSearchCV:
    """Pick C with grouped 5-fold cross-validation on the training set only."""
    search = GridSearchCV(
        build_pipeline(), {"clf__C": C_GRID}, scoring="f1_macro",
        cv=GroupKFold(n_splits=N_FOLDS), n_jobs=-1, refit=True,
    )
    return search.fit(train["instruction"], train["category"], groups=train["group_id"])


def cv_table(search: GridSearchCV) -> pd.DataFrame:
    """Mean and std of cross-validated macro-F1 for each C."""
    r = search.cv_results_
    return pd.DataFrame({
        "C": r["param_clf__C"],
        "cv macro-F1 mean": np.round(r["mean_test_score"], 4),
        "cv macro-F1 std": np.round(r["std_test_score"], 4),
    })


def confident_wrong(test: pd.DataFrame, pred: np.ndarray, conf: np.ndarray, n: int = 15) -> pd.DataFrame:
    """The n test rows where the model is wrong with the highest confidence."""
    t = test.assign(predicted=pred, confidence=np.round(conf, 3))
    wrong = t[t["predicted"] != t["category"]]
    cols = ["instruction", "category", "intent", "predicted", "confidence"]
    return wrong.sort_values("confidence", ascending=False).head(n)[cols]


def confusion_table(y_true: pd.Series, pred: np.ndarray, labels: list[str]) -> pd.DataFrame:
    """Confusion matrix with true labels as rows and predicted labels as columns."""
    cm = confusion_matrix(y_true, pred, labels=labels)
    return pd.DataFrame(cm, index=labels, columns=labels).rename_axis("true \\ pred").reset_index()


def report_table(y_true: pd.Series, pred: np.ndarray) -> pd.DataFrame:
    """Per-class precision, recall, F1 and support."""
    rep = classification_report(y_true, pred, output_dict=True, zero_division=0)
    rows = {k: v for k, v in rep.items() if k not in ("accuracy",)}
    return pd.DataFrame(rows).T.round(3).rename_axis("class").reset_index()


def similarity_bands(train: pd.DataFrame, test: pd.DataFrame, pred: np.ndarray) -> pd.DataFrame:
    """Test accuracy grouped by how similar each test row is to its closest train row."""
    vec = char_vectors(pd.concat([train["norm"], test["norm"]]))
    sims = max_similarity_to_train(train["norm"], test["norm"], vec)
    bands = pd.cut(sims, [0, 0.5, 0.6, 0.7, 0.8, 0.9])
    ok = pd.Series(pred == test["category"].to_numpy())
    t = ok.groupby(bands, observed=True).agg(["size", "mean"]).reset_index()
    t.columns = ["similarity to closest train row", "test rows", "accuracy"]
    t["accuracy"] = t["accuracy"].round(4)
    t["similarity to closest train row"] = t["similarity to closest train row"].astype(str)
    return t


def main() -> None:
    """Tune, fit on all of train, evaluate once on test, save model and report."""
    train = pd.read_parquet(DATA_DIR / "train.parquet")
    test = pd.read_parquet(DATA_DIR / "test.parquet")
    search = tune(train)
    model = search.best_estimator_
    proba = model.predict_proba(test["instruction"])
    pred = model.classes_[proba.argmax(axis=1)]
    conf = proba.max(axis=1)
    acc = accuracy_score(test["category"], pred)
    macro = f1_score(test["category"], pred, average="macro")
    labels = list(model.classes_)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    META_PATH.write_text(json.dumps({
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "best_C": search.best_params_["clf__C"],
        "classes": labels,
        "test_accuracy": round(acc, 4),
        "test_macro_f1": round(macro, 4),
    }, indent=2), encoding="utf-8")

    report = f"""# Category classifier

## Model

`normalise()` -> FeatureUnion(word 1-2-gram TF-IDF, char_wb 3-5-gram TF-IDF,
both sublinear_tf) -> LogisticRegression(max_iter=2000, class_weight="balanced").

Train {len(train):,} rows, test {len(test):,} rows (grouped split, see split.md).
scikit-learn {sklearn.__version__}.

## Choosing C (GroupKFold, {N_FOLDS} folds, training set only)

{md_table(cv_table(search))}

Best C: **{search.best_params_['clf__C']}**. The model was then refit on all of train.

## Test set (evaluated once)

- Accuracy: **{acc:.4f}**
- Macro-F1: **{macro:.4f}**

### Per class

{md_table(report_table(test['category'], pred))}

### Confusion matrix

{md_table(confusion_table(test['category'], pred, labels))}

### Does the score depend on near-copies?

If the score came from memorising near-copies, accuracy would drop on test rows that
are least similar to training. It does not drop much: the dataset is template-generated
and each category has very distinctive wording, so this test set is easy. The score on
hand-written messages (my_20.md) is the better guide to real-world performance.

{md_table(similarity_bands(train, test, pred))}

## 15 most confident wrong predictions

Read these for doubtful labels: sometimes the model is right and the label is not.

{md_table(confident_wrong(test, pred, conf))}

## Wrong predictions explained

_To be written by hand._
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"best_C={search.best_params_['clf__C']} test_accuracy={acc:.4f} "
          f"test_macro_f1={macro:.4f} -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
