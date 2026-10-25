"""
HealOS 2.0 - AI Predictive Model Training
Generates a reproducible synthetic telemetry dataset and trains a Random Forest
Classifier to estimate application crash risk under operating system stress.

Synthetic Risk Factors modeled:
- Memory leak patterns (RAM > 85% or rapid ram_change > +15%)
- Resource exhaustion storms (CPU > 88% and RAM > 80%)
- Severe storage saturation (Disk > 92%)
- Process table contention (Process count > 400 with positive delta)
"""

import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        confusion_matrix,
        classification_report,
    )
    from sklearn.model_selection import train_test_split
    ML_LIBRARIES_AVAILABLE = True
except ImportError as err:
    ML_LIBRARIES_AVAILABLE = False
    _IMPORT_ERROR_MSG = str(err)
    RandomForestClassifier = None

# Add root directory to sys.path if run directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (
    DATASET_FILE,
    MODEL_FILE,
    RANDOM_SEED,
    SYNTHETIC_DATASET_SIZE,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)


def generate_synthetic_dataset(
    n_samples: int = SYNTHETIC_DATASET_SIZE,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generates a reproducible synthetic dataset of operating system metrics
    and assigns binary failure_risk labels (0: Normal, 1: Failure Risk).
    """
    rng = np.random.default_rng(seed)

    # 1. Feature sampling using realistic distributions
    cpu = rng.uniform(5.0, 98.0, size=n_samples)
    ram = rng.uniform(15.0, 99.0, size=n_samples)
    disk = rng.uniform(20.0, 95.0, size=n_samples)
    process_count = rng.integers(60, 450, size=n_samples)

    # Changes between consecutive intervals (-30% to +35%)
    cpu_change = rng.normal(loc=0.0, scale=8.0, size=n_samples)
    cpu_change = np.clip(cpu_change, -40.0, 40.0)

    ram_change = rng.normal(loc=0.5, scale=6.0, size=n_samples)
    ram_change = np.clip(ram_change, -30.0, 30.0)

    # 2. Risk scoring heuristic (transparent ground truth for prototype classifier)
    # Failure risk is triggered by critical saturation or rapid surges
    risk_score = (
        (ram > 85.0).astype(float) * 2.5
        + (ram_change > 12.0).astype(float) * 2.0
        + ((cpu > 88.0) & (ram > 75.0)).astype(float) * 2.0
        + (cpu_change > 25.0).astype(float) * 1.5
        + (disk > 92.0).astype(float) * 1.5
        + (process_count > 380).astype(float) * 1.0
    )

    # Add Gaussian noise to model stochastic real-world anomalies
    noise = rng.normal(0.0, 0.4, size=n_samples)
    continuous_risk = risk_score + noise

    # Binary threshold: risk_score >= 2.0 indicates elevated crash probability
    labels = (continuous_risk >= 2.0).astype(int)

    df = pd.DataFrame(
        {
            "cpu_percent": np.round(cpu, 2),
            "ram_percent": np.round(ram, 2),
            "disk_percent": np.round(disk, 2),
            "process_count": process_count,
            "cpu_change": np.round(cpu_change, 2),
            "ram_change": np.round(ram_change, 2),
            TARGET_COLUMN: labels,
        }
    )

    return df


def train_failure_model(
    dataset_path: Path = DATASET_FILE,
    model_path: Path = MODEL_FILE,
    save_files: bool = True,
) -> Tuple[Optional[Any], Dict[str, Any]]:
    """
    Trains and evaluates the Random Forest failure risk predictor.
    Saves dataset to CSV and model artifact to PKL.
    """
    print("=" * 65)
    print(" HealOS 2.0: AI Predictive Failure Model Training Pipeline")
    print("=" * 65)

    if not ML_LIBRARIES_AVAILABLE:
        print("[!] ERROR: Machine learning packages are not installed in this environment.")
        print(f"    Missing dependency: {_IMPORT_ERROR_MSG}")
        print("[*] To train the model, activate the virtual environment:")
        print("    source venv/bin/activate   # on Linux / WSL")
        print("    pip install -r requirements.txt")
        print("=" * 65)
        return None, {}

    # 1. Generate or load dataset
    print(f"[*] Generating {SYNTHETIC_DATASET_SIZE} synthetic telemetry samples (seed={RANDOM_SEED})...")
    df = generate_synthetic_dataset(SYNTHETIC_DATASET_SIZE, RANDOM_SEED)

    risk_count = int(df[TARGET_COLUMN].sum())
    normal_count = len(df) - risk_count
    print(f"    - Normal samples : {normal_count} ({normal_count / len(df) * 100:.1f}%)")
    print(f"    - Risk samples   : {risk_count} ({risk_count / len(df) * 100:.1f}%)")

    # 2. Partition features and target
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # 3. Train / Test Split (80% train, 20% test) with fixed seed (no data leakage)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    print(f"[*] Data partition: Train={len(X_train)} samples, Test={len(X_test)} samples")

    # 4. Instantiate and fit Random Forest Classifier
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_SEED,
        class_weight="balanced",
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # 5. Evaluate on isolated test set
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    metrics = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1_score": float(f1),
        "confusion_matrix": cm.tolist(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    print("\n" + "-" * 40)
    print(" Model Evaluation Metrics (Test Set):")
    print("-" * 40)
    print(f"  Accuracy  : {acc * 100:.2f}%")
    print(f"  Precision : {prec * 100:.2f}%")
    print(f"  Recall    : {rec * 100:.2f}%")
    print(f"  F1-Score  : {f1 * 100:.2f}%")
    print("\nConfusion Matrix:")
    print(f"  [[TN={cm[0, 0]}, FP={cm[0, 1]}]")
    print(f"   [FN={cm[1, 0]}, TP={cm[1, 1]}]]")
    print("-" * 40)

    # Feature importances
    importances = dict(zip(FEATURE_COLUMNS, clf.feature_importances_))
    sorted_importances = sorted(importances.items(), key=lambda item: item[1], reverse=True)
    print("\nFeature Importances:")
    for feat, imp in sorted_importances:
        print(f"  - {feat:15s}: {imp * 100:.2f}%")

    # 6. Save artifacts
    if save_files:
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dataset_path, index=False)
        print(f"\n[+] Synthetic dataset saved to: {dataset_path}")

        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, model_path)
        print(f"[+] Trained model saved to   : {model_path}")

    print("=" * 65 + "\n")
    return clf, metrics


if __name__ == "__main__":
    train_failure_model()
