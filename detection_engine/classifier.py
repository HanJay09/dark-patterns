"""
detection_engine/classifier.py

ML text classifier for dark pattern detection.

Architecture: TF-IDF vectoriser + Logistic Regression
Why this choice (vs fine-tuned BERT)?
  - Trainable on small datasets (200–500 examples per class)
  - Fast inference (<100ms per page)
  - Fully explainable (top features are inspectable)
  - Easy to evaluate (standard sklearn metrics)
  - Lower risk for a prototype — BERT fine-tuning is listed as a stretch
    goal in the open questions (Q2 in the requirements doc)

The classifier operates on individual text snippets extracted from the page
(button text, paragraph text, form labels) rather than the whole page at once.
This gives per-instance evidence rather than a page-level probability.

Training:
  Run `python -m detection_engine.classifier train` with labelled data in
  data/labelled/training.csv (columns: text, label).
  The trained model is saved to data/models/classifier.pkl.

Inference:
  The engine loads the saved model at startup. If no model exists, the
  classifier is skipped and only rule-based hits are returned.
"""

from __future__ import annotations

import os
import pickle
import warnings
from pathlib import Path
from typing import Optional

LABELS = [
    'DP-1',   # Misdirection
    'DP-2',   # Hidden Costs
    'DP-3',   # Confirmshaming
    'DP-4',   # Disguised Ads
    'DP-5',   # Forced Continuity
    'DP-6',   # Urgency / Scarcity
    'NONE',   # No dark pattern
]

LABEL_TO_CATEGORY = {
    'DP-1': 'Misdirection',
    'DP-2': 'Hidden Costs',
    'DP-3': 'Confirmshaming',
    'DP-4': 'Disguised Ads',
    'DP-5': 'Forced Continuity',
    'DP-6': 'Urgency / Scarcity',
}

MODEL_PATH = Path(__file__).parent.parent / 'data' / 'models' / 'classifier.pkl'

# Minimum confidence threshold — predictions below this are discarded
CONFIDENCE_THRESHOLD = 0.55


class DarkPatternClassifier:
    """Thin wrapper around a sklearn Pipeline (TfidfVectorizer + LogisticRegression)."""

    def __init__(self):
        self.pipeline   = None
        self._available = False
        self._load()

    def _load(self):
        if MODEL_PATH.exists():
            with open(MODEL_PATH, 'rb') as f:
                self.pipeline   = pickle.load(f)
                self._available = True
            print(f"[classifier] Loaded model from {MODEL_PATH}")
        else:
            print(
                f"[classifier] No trained model found at {MODEL_PATH}. "
                "Only rule-based detection will run. "
                "Train a model with: python -m detection_engine.classifier train"
            )

    @property
    def available(self) -> bool:
        return self._available

    def predict(self, texts: list[str]) -> list[dict]:
        """
        Classify a list of text snippets.
        Returns a list of dicts with keys: text, label, confidence.
        Only returns results where label != 'NONE' and confidence >= threshold.
        """
        if not self._available or not texts:
            return []

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            probs  = self.pipeline.predict_proba(texts)
            labels = self.pipeline.classes_

        results = []
        for text, prob_row in zip(texts, probs):
            idx        = prob_row.argmax()
            label      = labels[idx]
            confidence = float(prob_row[idx])

            if label != 'NONE' and confidence >= CONFIDENCE_THRESHOLD:
                results.append({
                    'text':       text,
                    'label':      label,
                    'category':   LABEL_TO_CATEGORY.get(label, label),
                    'confidence': round(confidence, 3),
                })

        return results


# ── Training script ───────────────────────────────────────────────────────────

def train(csv_path: Optional[str] = None):
    """
    Train the classifier on labelled data and save to MODEL_PATH.

    CSV format expected:
        text,label
        "Only 3 left in stock",DP-6
        "No thanks I don't want to save",DP-3
        ...

    Run with:
        python -m detection_engine.classifier train
        python -m detection_engine.classifier train path/to/custom.csv
    """
    try:
        import pandas as pd
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        from sklearn.metrics import classification_report
    except ImportError:
        print("Training requires: pip install scikit-learn pandas")
        return

    default_csv = Path(__file__).parent.parent / 'data' / 'labelled' / 'training.csv'
    data_path   = Path(csv_path) if csv_path else default_csv

    if not data_path.exists():
        print(f"Training data not found at {data_path}")
        print("Create data/labelled/training.csv with columns: text, label")
        print(f"Valid labels: {', '.join(LABELS)}")
        return

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} training examples")
    print(df['label'].value_counts().to_string())

    X = df['text'].astype(str).tolist()
    y = df['label'].astype(str).tolist()

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=10_000,
            sublinear_tf=True,
            strip_accents='unicode',
            analyzer='word',
            min_df=1,
        )),
        ('clf', LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight='balanced',
            solver='lbfgs',
            multi_class='multinomial',
        )),
    ])

    # Cross-validation
    scores = cross_val_score(pipeline, X, y, cv=5, scoring='f1_macro')
    print(f"\nCV F1 (macro): {scores.mean():.3f} ± {scores.std():.3f}")

    # Train on full data
    pipeline.fit(X, y)

    # Save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(pipeline, f)
    print(f"\nModel saved to {MODEL_PATH}")


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'train':
        csv_arg = sys.argv[2] if len(sys.argv) > 2 else None
        train(csv_arg)
    else:
        print("Usage: python -m detection_engine.classifier train [path/to/data.csv]")


# Singleton — loaded once at import time
_classifier = None

def get_classifier() -> DarkPatternClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DarkPatternClassifier()
    return _classifier
