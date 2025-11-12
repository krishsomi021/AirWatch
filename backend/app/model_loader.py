"""Load and manage trained ML model."""
import joblib
import logging
from pathlib import Path
from typing import Optional, List, Dict
import numpy as np

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load and cache trained model for predictions."""
    
    def __init__(self, model_path: str, feature_list_path: str):
        """
        Initialize model loader.
        
        Args:
            model_path: Path to saved model file
            feature_list_path: Path to feature list file
        """
        self.model_path = Path(model_path)
        self.feature_list_path = Path(feature_list_path)
        self.model = None
        self.feature_names = None
        self._loaded = False
    
    def load(self):
        """Load model and feature list from disk."""
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.model = joblib.load(self.model_path)
            
            logger.info(f"Loading feature list from {self.feature_list_path}")
            self.feature_names = joblib.load(self.feature_list_path)
            
            self._loaded = True
            logger.info(f"Model loaded successfully with {len(self.feature_names)} features")
            
        except FileNotFoundError as e:
            logger.error(f"Model files not found: {e}")
            logger.error("Please train the model first using: python backend/app/ml/train.py")
            raise
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded
    
    def predict(self, features: Dict) -> Dict:
        """
        Make prediction using loaded model.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Dictionary with prediction results
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        # Ensure all features are present
        feature_vector = []
        for feat_name in self.feature_names:
            if feat_name in features:
                feature_vector.append(features[feat_name])
            else:
                logger.warning(f"Feature {feat_name} not provided, using 0")
                feature_vector.append(0.0)
        
        # Convert to numpy array and reshape for single prediction
        X = np.array(feature_vector).reshape(1, -1)
        
        # Get prediction probability
        proba = self.model.predict_proba(X)[0, 1]
        
        # Get feature importances if available
        feature_importance = self._get_feature_importance()
        
        return {
            'probability': float(proba),
            'feature_importance': feature_importance
        }
    
    def _get_feature_importance(self) -> Optional[Dict]:
        """Get feature importance from model if available."""
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            
            # Get top 5 features
            top_indices = np.argsort(importances)[::-1][:5]
            top_features = {
                self.feature_names[i]: float(importances[i])
                for i in top_indices
            }
            return top_features
        return None
    
    def get_top_factors(self, features: Dict, threshold: float = 0.40) -> List[str]:
        """
        Get human-readable explanation of top factors influencing prediction.
        
        Args:
            features: Feature dictionary
            threshold: Classification threshold
            
        Returns:
            List of factor descriptions
        """
        factors = []
        
        # Check key features
        if 'AQI_prev1' in features:
            aqi_prev = features['AQI_prev1']
            if aqi_prev > 80:
                factors.append(f"High previous day AQI ({aqi_prev:.0f})")
            elif aqi_prev < 30:
                factors.append(f"Low previous day AQI ({aqi_prev:.0f})")
        
        if 'wind_avg' in features:
            wind = features['wind_avg']
            if wind < 5:
                factors.append(f"Low wind speed ({wind:.1f} mph) - poor dispersion")
            elif wind > 12:
                factors.append(f"Good wind conditions ({wind:.1f} mph)")
        
        if 'precip' in features and 'has_rain' in features:
            if features['has_rain'] > 0:
                factors.append("Recent precipitation - cleaner air")
            else:
                factors.append("No recent rain - particles not washed out")
        
        if 'temp_max' in features:
            temp = features['temp_max']
            if temp > 85:
                factors.append(f"High temperature ({temp:.0f}°F) - increased emissions")
        
        if 'AQI_3day_avg' in features:
            avg_aqi = features['AQI_3day_avg']
            if avg_aqi > 60:
                factors.append(f"Elevated 3-day average AQI ({avg_aqi:.0f})")
        
        if 'is_weekend' in features and features['is_weekend'] == 1:
            factors.append("Weekend - typically lower emissions")
        
        # If no specific factors identified
        if not factors:
            factors.append("Multiple moderate factors")
        
        return factors[:3]  # Return top 3


# Global model instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader(model_path: str = None, feature_list_path: str = None) -> ModelLoader:
    """Get singleton model loader instance."""
    global _model_loader
    
    if _model_loader is None:
        if model_path is None or feature_list_path is None:
            raise ValueError("Model paths must be provided for first initialization")
        _model_loader = ModelLoader(model_path, feature_list_path)
        _model_loader.load()
    
    return _model_loader
