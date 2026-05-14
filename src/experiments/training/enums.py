"""Shared enum types for training configuration and orchestration."""

from enum import StrEnum


class ModelFamily(StrEnum):
    """Supported model families for training."""

    DECISION_TREE = "decision_tree"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SVM = "svm"
    NEURAL_NETWORK = "neural_network"


class TrainingMetric(StrEnum):
    """Supported metric keys for GridSearch scoring and reporting."""

    ACCURACY = "accuracy"
    BALANCED_ACCURACY = "balanced_accuracy"
    PRECISION_MACRO = "precision_macro"
    PRECISION_MICRO = "precision_micro"
    PRECISION_WEIGHTED = "precision_weighted"
    RECALL_MACRO = "recall_macro"
    RECALL_MICRO = "recall_micro"
    RECALL_WEIGHTED = "recall_weighted"
    F1_MACRO = "f1_macro"
    F1_MICRO = "f1_micro"
    F1_WEIGHTED = "f1_weighted"


class DecisionTreeCriterion(StrEnum):
    """Supported DecisionTreeClassifier criterion values."""

    GINI = "gini"
    ENTROPY = "entropy"


class GradientBoostingCriterion(StrEnum):
    """Supported GradientBoostingClassifier criterion values."""

    FRIEDMAN_MSE = "friedman_mse"
    SQUARED_ERROR = "squared_error"


class SvmKernel(StrEnum):
    """Supported SVC kernel options."""

    LINEAR = "linear"
    RBF = "rbf"


class SvmGamma(StrEnum):
    """Supported SVC gamma modes."""

    SCALE = "scale"
    AUTO = "auto"


class RandomForestMaxFeatures(StrEnum):
    """Supported RandomForestClassifier max_features options."""

    SQRT = "sqrt"
    LOG2 = "log2"


class NeuralOptimizer(StrEnum):
    """Supported PyTorch optimizer names for NN training."""

    ADAM = "adam"
    SGD = "sgd"


class HiddenActivation(StrEnum):
    """Supported hidden-layer activation names for NN training."""

    RELU = "relu"
    SIGMOID = "sigmoid"
