"""Train the crop-recommendation neural network used by the API.

Produces the three artifacts ModelManager expects in backend/models/crop/:
    - baseline_42crops.hdf5        torch state_dict for Net_64_128_64(7, 41)
    - encoder_42crops.pkl          sklearn LabelEncoder over the 41 crop labels
    - normalization_42crops.npz    {"mean": float32[7], "std": float32[7]}

Feature order (must match app/main.py predict_crop):
    N, P, K, temperature, humidity, ph, rainfall

Usage:
    python train_crop_model.py
"""

import os
import pickle

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(BASE_DIR, "data", "crops", "crop_recommendation.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models", "crop")
MODEL_PATH = os.path.join(MODEL_DIR, "baseline_42crops.hdf5")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoder_42crops.pkl")
NORM_PATH = os.path.join(MODEL_DIR, "normalization_42crops.npz")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
SEED = 42
EPOCHS = 400
BATCH_SIZE = 64
LR = 1e-3


class CropNet(nn.Module):
    """Same layer geometry as app.main.Net_64_128_64 (logits for training)."""

    def __init__(self, input_size: int, num_classes: int):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 128)
        self.fc3 = nn.Linear(128, 64)
        self.fc4 = nn.Linear(64, num_classes)

    def forward(self, x):
        x = torch.selu(self.fc1(x))
        x = torch.selu(self.fc2(x))
        x = torch.selu(self.fc3(x))
        return self.fc4(x)


def main() -> int:
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    df = pd.read_csv(DATA_CSV)
    X = df[FEATURES].to_numpy(dtype=np.float32)
    labels = df["label"].astype(str).to_numpy()

    encoder = LabelEncoder()
    y = encoder.fit_transform(labels).astype(np.int64)
    num_classes = len(encoder.classes_)
    print(f"Rows: {len(df)} | features: {len(FEATURES)} | classes: {num_classes}")
    if num_classes != 41:
        print(f"WARNING: expected 41 classes to match Net(7, 41); got {num_classes}")

    mean = X.mean(axis=0).astype(np.float32)
    std = X.std(axis=0).astype(np.float32)
    std[std == 0] = 1.0  # guard against constant features

    Xn = (X - mean) / std

    X_tr, X_va, y_tr, y_va = train_test_split(
        Xn, y, test_size=0.2, random_state=SEED, stratify=y
    )

    device = torch.device("cpu")
    model = CropNet(len(FEATURES), num_classes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()

    Xtr_t = torch.tensor(X_tr, dtype=torch.float32)
    ytr_t = torch.tensor(y_tr, dtype=torch.long)
    Xva_t = torch.tensor(X_va, dtype=torch.float32)
    yva_t = torch.tensor(y_va, dtype=torch.long)

    best_acc, best_state = 0.0, None
    n = len(Xtr_t)
    for epoch in range(1, EPOCHS + 1):
        model.train()
        perm = torch.randperm(n)
        for i in range(0, n, BATCH_SIZE):
            idx = perm[i:i + BATCH_SIZE]
            opt.zero_grad()
            loss = loss_fn(model(Xtr_t[idx]), ytr_t[idx])
            loss.backward()
            opt.step()

        if epoch % 20 == 0 or epoch == EPOCHS:
            model.eval()
            with torch.no_grad():
                acc = (model(Xva_t).argmax(1) == yva_t).float().mean().item()
            if acc > best_acc:
                best_acc = acc
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            print(f"epoch {epoch:3d} | val acc {acc:.4f} | best {best_acc:.4f}")

    model.load_state_dict(best_state)
    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump(encoder, f)
    np.savez(NORM_PATH, mean=mean, std=std)

    print(f"\nSaved:\n  {MODEL_PATH}\n  {ENCODER_PATH}\n  {NORM_PATH}")
    print(f"Best validation accuracy: {best_acc:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
