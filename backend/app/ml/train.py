"""Train the AQI classification model."""
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import logging
from datetime import datetime
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_recall_curve, auc, roc_auc_score, brier_score_loss
)
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.ml.features import FeatureEngineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AQIModelTrainer:
    """Train and evaluate AQI classification models."""
    
    def __init__(self, data_path: Path, artifacts_dir: Path):
        """
        Initialize trainer.
        
        Args:
            data_path: Path to training data CSV
            artifacts_dir: Directory to save model artifacts
        """
        self.data_path = data_path
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.feature_names = []
        self.threshold = 0.5
    
    def load_and_prepare_data(self) -> tuple:
        """Load and prepare training data."""
        logger.info(f"Loading data from {self.data_path}")
        
        # Load data
        df = pd.read_csv(self.data_path, parse_dates=['Date'])
        logger.info(f"Loaded {len(df)} records")
        
        # Engineer features
        logger.info("Engineering features...")
        df = self.feature_engineer.create_features(df, is_training=True)
        
        # Prepare for training
        X, y, feature_names = self.feature_engineer.prepare_for_training(df)
        self.feature_names = feature_names
        
        logger.info(f"Prepared {len(X)} samples with {len(feature_names)} features")
        logger.info(f"Class distribution: {y.value_counts().to_dict()}")
        
        return X, y
    
    def train_baseline(self, X_train, y_train):
        """Train baseline logistic regression model."""
        logger.info("Training baseline logistic regression...")
        
        model = LogisticRegression(
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        return model
    
    def train_lightgbm(self, X_train, y_train):
        """Train LightGBM model (primary model)."""
        logger.info("Training LightGBM model...")
        
        # Calculate scale_pos_weight for imbalanced data
        neg_count = (y_train == 0).sum()
        pos_count = (y_train == 1).sum()
        scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
        
        logger.info(f"Scale pos weight: {scale_pos_weight:.2f}")
        
        model = LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            verbose=-1
        )
        model.fit(X_train, y_train)
        
        return model
    
    def train_random_forest(self, X_train, y_train):
        """Train Random Forest model (comparison)."""
        logger.info("Training Random Forest model...")
        
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        return model
    
    def evaluate_model(self, model, X_test, y_test, model_name: str = "Model"):
        """Evaluate model and print metrics."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluating {model_name}")
        logger.info(f"{'='*60}")
        
        # Predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        # Classification report
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred, 
                                         target_names=['Safe', 'Unhealthy']))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info("\nConfusion Matrix:")
        logger.info(f"              Predicted")
        logger.info(f"              Safe  Unhealthy")
        logger.info(f"Actual Safe   {cm[0, 0]:<6} {cm[0, 1]:<6}")
        logger.info(f"       Unhealthy {cm[1, 0]:<6} {cm[1, 1]:<6}")
        
        # Precision-Recall AUC
        precision, recall, _ = precision_recall_curve(y_test, y_proba)
        pr_auc = auc(recall, precision)
        logger.info(f"\nPR-AUC: {pr_auc:.4f}")
        
        # ROC-AUC
        roc_auc = roc_auc_score(y_test, y_proba)
        logger.info(f"ROC-AUC: {roc_auc:.4f}")
        
        # Brier Score (calibration)
        brier = brier_score_loss(y_test, y_proba)
        logger.info(f"Brier Score: {brier:.4f} (lower is better)")
        
        return {
            'pr_auc': pr_auc,
            'roc_auc': roc_auc,
            'brier_score': brier,
            'confusion_matrix': cm,
            'y_proba': y_proba,
            'precision': precision,
            'recall': recall
        }
    
    def find_optimal_threshold(self, y_test, y_proba, target_recall: float = 0.80):
        """Find optimal classification threshold to achieve target recall."""
        precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
        
        # Find threshold that achieves target recall
        valid_idx = recall >= target_recall
        if valid_idx.any():
            best_idx = np.where(valid_idx)[0][-1]  # Last index meeting recall
            optimal_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
            optimal_precision = precision[best_idx]
            optimal_recall = recall[best_idx]
            
            logger.info(f"\nOptimal threshold for {target_recall:.0%} recall: {optimal_threshold:.3f}")
            logger.info(f"Achieves Precision: {optimal_precision:.3f}, Recall: {optimal_recall:.3f}")
            
            return optimal_threshold
        else:
            logger.warning(f"Could not achieve {target_recall:.0%} recall")
            return 0.5
    
    def plot_pr_curve(self, results: dict, save_path: Path):
        """Plot Precision-Recall curve."""
        plt.figure(figsize=(8, 6))
        plt.plot(results['recall'], results['precision'], linewidth=2)
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title(f'Precision-Recall Curve (AUC={results["pr_auc"]:.3f})', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150)
        logger.info(f"Saved PR curve to {save_path}")
        plt.close()
    
    def plot_feature_importance(self, model, save_path: Path, top_n: int = 20):
        """Plot feature importance for tree-based models."""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1][:top_n]
            
            plt.figure(figsize=(10, 8))
            plt.barh(range(top_n), importances[indices])
            plt.yticks(range(top_n), [self.feature_names[i] for i in indices])
            plt.xlabel('Importance', fontsize=12)
            plt.title('Top Feature Importances', fontsize=14)
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(save_path, dpi=150)
            logger.info(f"Saved feature importance plot to {save_path}")
            plt.close()
    
    def train_and_evaluate(self, test_size: float = 0.2, use_cv: bool = False):
        """
        Full training and evaluation pipeline.
        
        Args:
            test_size: Fraction of data for testing
            use_cv: Whether to use time series cross-validation
        """
        # Load data
        X, y = self.load_and_prepare_data()
        
        # Time-based train/test split
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        logger.info(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")
        
        # Train models
        models = {
            'Logistic Regression': self.train_baseline(X_train, y_train),
            'LightGBM': self.train_lightgbm(X_train, y_train),
            'Random Forest': self.train_random_forest(X_train, y_train)
        }
        
        # Evaluate all models
        results = {}
        for name, model in models.items():
            results[name] = self.evaluate_model(model, X_test, y_test, name)
        
        # Select best model (by PR-AUC)
        best_model_name = max(results, key=lambda k: results[k]['pr_auc'])
        best_model = models[best_model_name]
        best_results = results[best_model_name]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Best Model: {best_model_name} (PR-AUC: {best_results['pr_auc']:.4f})")
        logger.info(f"{'='*60}")
        
        # Find optimal threshold
        self.model = best_model
        self.threshold = self.find_optimal_threshold(
            y_test, 
            best_results['y_proba'],
            target_recall=0.80
        )
        
        # Save artifacts
        self.save_model()
        
        # Create plots
        self.plot_pr_curve(best_results, self.artifacts_dir / 'pr_curve.png')
        self.plot_feature_importance(best_model, self.artifacts_dir / 'feature_importance.png')
        
        return best_model, best_results
    
    def save_model(self):
        """Save trained model and metadata."""
        model_path = self.artifacts_dir / 'aqi_model.pkl'
        feature_path = self.artifacts_dir / 'feature_list.pkl'
        metadata_path = self.artifacts_dir / 'model_metadata.txt'
        
        # Save model
        joblib.dump(self.model, model_path)
        logger.info(f"Saved model to {model_path}")
        
        # Save feature list
        joblib.dump(self.feature_names, feature_path)
        logger.info(f"Saved feature list to {feature_path}")
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            f.write(f"Model trained: {datetime.now()}\n")
            f.write(f"Model type: {type(self.model).__name__}\n")
            f.write(f"Number of features: {len(self.feature_names)}\n")
            f.write(f"Optimal threshold: {self.threshold:.4f}\n")
            f.write(f"\nFeature names:\n")
            for feat in self.feature_names:
                f.write(f"  - {feat}\n")
        
        logger.info(f"Saved metadata to {metadata_path}")


def create_sample_data():
    """Create sample training data for demonstration."""
    np.random.seed(42)
    n_samples = 1000
    
    # Generate dates
    dates = pd.date_range('2020-01-01', periods=n_samples, freq='D')
    
    # Generate synthetic AQI data with patterns
    base_aqi = 40 + 20 * np.sin(np.arange(n_samples) * 2 * np.pi / 365)  # Seasonal
    noise = np.random.normal(0, 10, n_samples)
    spikes = np.random.binomial(1, 0.05, n_samples) * np.random.uniform(60, 100, n_samples)
    aqi = np.clip(base_aqi + noise + spikes, 0, 300)
    
    # Weather features
    temp = 50 + 30 * np.sin(np.arange(n_samples) * 2 * np.pi / 365) + np.random.normal(0, 5, n_samples)
    wind = np.abs(np.random.normal(8, 3, n_samples))
    precip = np.random.exponential(0.1, n_samples)
    humidity = 50 + 20 * np.sin(np.arange(n_samples) * 2 * np.pi / 365) + np.random.normal(0, 10, n_samples)
    
    df = pd.DataFrame({
        'Date': dates,
        'AQI': aqi,
        'temp_max': temp,
        'wind_avg': wind,
        'precip': precip,
        'rh_avg': humidity
    })
    
    return df


if __name__ == '__main__':
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    artifacts_dir = project_root / 'app' / 'ml' / 'artifacts'
    
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample data if no real data exists
    data_path = data_dir / 'processed' / 'training_data.csv'
    if not data_path.exists():
        logger.info("Creating sample training data...")
        sample_df = create_sample_data()
        data_path.parent.mkdir(parents=True, exist_ok=True)
        sample_df.to_csv(data_path, index=False)
        logger.info(f"Saved sample data to {data_path}")
    
    # Train model
    trainer = AQIModelTrainer(data_path, artifacts_dir)
    model, results = trainer.train_and_evaluate(test_size=0.2)
    
    logger.info("\n✓ Training complete! Model saved to artifacts directory.")
