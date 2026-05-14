"""Model builders and GridSearch parameter spaces."""

from typing import Any

import numpy as np
import torch
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src.config import settings
from src.experiments.training.enums import (
    HiddenActivation,
    ModelFamily,
    NeuralOptimizer,
)
from src.experiments.training.schemas import ModelSpec


class TorchMulticlassClassifier(BaseEstimator, ClassifierMixin):
    """Minimal PyTorch multiclass estimator compatible with GridSearchCV."""

    def __init__(
        self,
        hidden_layer_sizes: tuple[int, ...] = (64,),
        hidden_activation: HiddenActivation | str = HiddenActivation.RELU,
        optimizer_name: NeuralOptimizer | str = NeuralOptimizer.ADAM,
        learning_rate: float = 0.001,
        l2_alpha: float = 0.0001,
        epochs: int = 50,
        batch_size: int = 32,
        verbose: int = 0,
    ) -> None:
        """Initialize with hyperparameters."""
        self.hidden_layer_sizes = hidden_layer_sizes
        self.hidden_activation = hidden_activation
        self.optimizer_name = optimizer_name
        self.learning_rate = learning_rate
        self.l2_alpha = l2_alpha
        self.epochs = epochs
        self.batch_size = batch_size
        self.verbose = verbose

    def _activation_layer(self) -> nn.Module:
        """Map activation name to torch activation module."""
        activation = HiddenActivation(self.hidden_activation)
        match activation:
            case HiddenActivation.RELU:
                return nn.ReLU()
            case HiddenActivation.SIGMOID:
                return nn.Sigmoid()
        raise ValueError(f"Unsupported hidden activation '{self.hidden_activation}'.")

    def fit(self, x: np.ndarray, y: np.ndarray) -> "TorchMulticlassClassifier":
        """Fit PyTorch multiclass classifier."""
        torch.manual_seed(settings.random_seed)

        x_array = np.asarray(x, dtype=np.float32)
        y_raw = np.asarray(y).reshape(-1)
        classes, y_indices = np.unique(y_raw, return_inverse=True)
        y_array = y_indices.astype(np.int64)
        input_dim = x_array.shape[1]
        output_dim = len(classes)

        hidden_sizes = tuple(int(size) for size in self.hidden_layer_sizes)
        if len(hidden_sizes) != 1:
            raise ValueError(
                "hidden_layer_sizes must contain exactly one layer size, e.g. (64,)."
            )
        if any(size <= 0 for size in hidden_sizes):
            raise ValueError("hidden_layer_sizes values must be positive integers.")
        layers: list[nn.Module] = []
        prev_dim = input_dim
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_dim, hidden_size))
            layers.append(self._activation_layer())
            prev_dim = hidden_size
        layers.append(nn.Linear(prev_dim, output_dim))
        model = nn.Sequential(*layers)

        optimizer_name = NeuralOptimizer(self.optimizer_name)
        match optimizer_name:
            case NeuralOptimizer.ADAM:
                optimizer = torch.optim.Adam(
                    model.parameters(),
                    lr=self.learning_rate,
                    weight_decay=self.l2_alpha,
                )
            case NeuralOptimizer.SGD:
                optimizer = torch.optim.SGD(
                    model.parameters(),
                    lr=self.learning_rate,
                    weight_decay=self.l2_alpha,
                )
            case _:
                raise ValueError(
                    f"Unsupported torch optimizer '{self.optimizer_name}'."
                )

        criterion = nn.CrossEntropyLoss()
        dataset = TensorDataset(
            torch.from_numpy(x_array),
            torch.from_numpy(y_array),
        )
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        model.train()
        for _ in range(self.epochs):
            for x_batch, y_batch in dataloader:
                optimizer.zero_grad()
                logits = model(x_batch)
                loss = criterion(logits, y_batch.long())
                loss.backward()
                optimizer.step()

        self.model_ = model
        self.classes_ = classes
        return self

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        x_array = np.asarray(x, dtype=np.float32)
        x_tensor = torch.from_numpy(x_array)
        self.model_.eval()
        with torch.no_grad():
            logits = self.model_(x_tensor)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()
        return probabilities

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        probabilities = self.predict_proba(x)
        class_indices = probabilities.argmax(axis=1)
        return self.classes_[class_indices]


def _validate_non_empty_grid(
    param_grid: dict[str, list[Any]], model_family: ModelFamily
) -> None:
    """Validate that every grid key has at least one candidate value."""
    empty = [key for key, values in param_grid.items() if not values]
    if empty:
        raise ValueError(f"Empty GridSearch values for {model_family}: {empty}")


def _build_nn_hidden_layer_sizes(n_features: int) -> list[tuple[int, ...]]:
    """Create one-hidden-layer size tuples from configured multipliers."""
    return [
        (max(1, round(multiplier * n_features)),)
        for multiplier in settings.training_nn_hidden_layer_multipliers
    ]


def build_model_spec(model_family: ModelFamily, *, n_features: int) -> ModelSpec:
    """Build model pipeline and GridSearchCV parameter grid for one family."""
    match model_family:
        case ModelFamily.DECISION_TREE:
            pipeline = Pipeline(
                steps=[
                    (
                        "model",
                        DecisionTreeClassifier(random_state=settings.random_seed),
                    )
                ]
            )
            min_samples_split_values = settings.training_dt_min_samples_split_values
            dt_param_grid: dict[str, list[Any]] = {
                "model__max_depth": settings.training_dt_max_depth_values,
                "model__min_samples_split": min_samples_split_values,
                "model__min_samples_leaf": settings.training_dt_min_samples_leaf_values,
                "model__criterion": settings.training_dt_criterion_values,
            }
            _validate_non_empty_grid(dt_param_grid, model_family)
            return ModelSpec(pipeline=pipeline, param_grid=dt_param_grid)

        case ModelFamily.RANDOM_FOREST:
            pipeline = Pipeline(
                steps=[
                    (
                        "model",
                        RandomForestClassifier(
                            random_state=settings.random_seed,
                            n_jobs=settings.training_gridsearch_n_jobs,
                        ),
                    )
                ]
            )
            min_samples_split_values = settings.training_rf_min_samples_split_values
            rf_param_grid: dict[str, list[Any]] = {
                "model__n_estimators": settings.training_rf_n_estimators_values,
                "model__max_depth": settings.training_rf_max_depth_values,
                "model__min_samples_split": min_samples_split_values,
                "model__min_samples_leaf": settings.training_rf_min_samples_leaf_values,
                "model__max_features": settings.training_rf_max_features_values,
            }
            _validate_non_empty_grid(rf_param_grid, model_family)
            return ModelSpec(pipeline=pipeline, param_grid=rf_param_grid)

        case ModelFamily.GRADIENT_BOOSTING:
            pipeline = Pipeline(
                steps=[
                    (
                        "model",
                        GradientBoostingClassifier(random_state=settings.random_seed),
                    )
                ]
            )
            gb_param_grid: dict[str, list[Any]] = {
                "model__n_estimators": settings.training_gb_n_estimators_values,
                "model__learning_rate": settings.training_gb_learning_rate_values,
                "model__max_depth": settings.training_gb_max_depth_values,
                "model__subsample": settings.training_gb_subsample_values,
                "model__min_samples_leaf": settings.training_gb_min_samples_leaf_values,
                "model__criterion": settings.training_gb_criterion_values,
            }
            _validate_non_empty_grid(gb_param_grid, model_family)
            return ModelSpec(pipeline=pipeline, param_grid=gb_param_grid)

        case ModelFamily.SVM:
            pipeline = Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        SVC(),
                    ),
                ]
            )
            svm_param_grid: dict[str, list[Any]] = {
                "model__C": settings.training_svm_c_values,
                "model__kernel": settings.training_svm_kernel_values,
                "model__gamma": settings.training_svm_gamma_values,
            }
            _validate_non_empty_grid(svm_param_grid, model_family)
            return ModelSpec(pipeline=pipeline, param_grid=svm_param_grid)

        case ModelFamily.NEURAL_NETWORK:
            pipeline = Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        TorchMulticlassClassifier(),
                    ),
                ]
            )
            hidden_activation_values = settings.training_nn_hidden_activation_values
            nn_param_grid: dict[str, list[Any]] = {
                "model__hidden_layer_sizes": _build_nn_hidden_layer_sizes(n_features),
                "model__hidden_activation": hidden_activation_values,
                "model__optimizer_name": settings.training_nn_solver_values,
                "model__learning_rate": settings.training_nn_learning_rate_init_values,
                "model__l2_alpha": settings.training_nn_alpha_values,
                "model__epochs": settings.training_nn_max_iter_values,
                "model__batch_size": settings.training_nn_batch_size_values,
            }
            _validate_non_empty_grid(nn_param_grid, model_family)
            return ModelSpec(pipeline=pipeline, param_grid=nn_param_grid)
    raise ValueError(f"Unsupported model family: {model_family}")
