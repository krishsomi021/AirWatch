"""Feature engineering for AQI prediction."""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict


class FeatureEngineer:
    """Create features for AQI prediction model."""
    
    def __init__(self):
        """Initialize feature engineer."""
        self.feature_names = []
    
    def create_features(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Create all features for the model.
        
        Args:
            df: DataFrame with raw data
            is_training: Whether this is for training (affects lag feature creation)
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # Ensure date column is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
        
        # Create lag features
        df = self._create_lag_features(df, is_training)
        
        # Create rolling features
        df = self._create_rolling_features(df, is_training)
        
        # Create temporal features
        df = self._create_temporal_features(df)
        
        # Create weather interaction features
        df = self._create_weather_features(df)
        
        # Create label if training
        if is_training and 'AQI' in df.columns:
            df['label_unhealthy'] = (df['AQI'] >= 101).astype(int)
        
        return df
    
    def _create_lag_features(self, df: pd.DataFrame, is_training: bool) -> pd.DataFrame:
        """Create lagged AQI features."""
        if 'AQI' not in df.columns:
            return df
        
        # Previous day AQI
        df['AQI_prev1'] = df['AQI'].shift(1)
        
        # Two days ago AQI
        df['AQI_prev2'] = df['AQI'].shift(2)
        
        # Previous week same day (7 days ago)
        df['AQI_prev7'] = df['AQI'].shift(7)
        
        return df
    
    def _create_rolling_features(self, df: pd.DataFrame, is_training: bool) -> pd.DataFrame:
        """Create rolling window features."""
        if 'AQI' not in df.columns:
            return df
        
        # 3-day rolling average (shifted to avoid leakage)
        df['AQI_3day_avg'] = df['AQI'].rolling(window=3, min_periods=1).mean().shift(1)
        
        # 7-day rolling average
        df['AQI_7day_avg'] = df['AQI'].rolling(window=7, min_periods=1).mean().shift(1)
        
        # 3-day rolling max
        df['AQI_3day_max'] = df['AQI'].rolling(window=3, min_periods=1).max().shift(1)
        
        # Standard deviation (volatility)
        df['AQI_7day_std'] = df['AQI'].rolling(window=7, min_periods=2).std().shift(1)
        
        # Trend: difference from 7-day average
        df['AQI_trend'] = df['AQI_prev1'] - df['AQI_7day_avg']
        
        return df
    
    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features."""
        if 'Date' not in df.columns:
            return df
        
        df['month'] = df['Date'].dt.month
        df['day_of_week'] = df['Date'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['day_of_year'] = df['Date'].dt.dayofyear
        
        # Season
        df['season'] = df['month'] % 12 // 3  # 0=winter, 1=spring, 2=summer, 3=fall
        
        # Holiday flag (simplified - major holidays)
        df['is_holiday'] = self._is_holiday(df['Date'])
        
        # Cyclical encoding for month
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Cyclical encoding for day of week
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
    
    def _is_holiday(self, dates: pd.Series) -> pd.Series:
        """Simple holiday detection for major US holidays."""
        # This is a simplified version - could use holidays library for accuracy
        is_holiday = pd.Series(False, index=dates.index)
        
        for date in dates:
            if pd.isna(date):
                continue
            # July 4th
            if date.month == 7 and date.day == 4:
                is_holiday[dates == date] = True
            # New Year's Day
            elif date.month == 1 and date.day == 1:
                is_holiday[dates == date] = True
            # Christmas
            elif date.month == 12 and date.day == 25:
                is_holiday[dates == date] = True
        
        return is_holiday.astype(int)
    
    def _create_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create weather-related features and interactions."""
        # Temperature bins
        if 'temp_max' in df.columns:
            df['temp_bin'] = pd.cut(df['temp_max'], 
                                     bins=[-np.inf, 32, 50, 70, 90, np.inf],
                                     labels=[0, 1, 2, 3, 4]).astype(float)
        
        # Wind categories
        if 'wind_avg' in df.columns:
            df['wind_category'] = pd.cut(df['wind_avg'],
                                          bins=[-np.inf, 5, 10, 15, np.inf],
                                          labels=[0, 1, 2, 3]).astype(float)
            
            # Stagnation indicator (low wind)
            df['is_stagnant'] = (df['wind_avg'] < 5).astype(int)
        
        # Rain flag
        if 'precip' in df.columns:
            df['has_rain'] = (df['precip'] > 0.1).astype(int)
        
        # Interaction: high temp + low wind = poor dispersion
        if 'temp_max' in df.columns and 'wind_avg' in df.columns:
            df['temp_wind_ratio'] = df['temp_max'] / (df['wind_avg'] + 1)
        
        # Humidity categories
        if 'rh_avg' in df.columns:
            df['humidity_high'] = (df['rh_avg'] > 70).astype(int)
        
        return df
    
    def get_feature_names(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature column names (excluding target and metadata)."""
        exclude_cols = ['Date', 'AQI', 'label_unhealthy', 'Site', 'County', 
                       'State', 'DAILY_AQI_VALUE']
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        return feature_cols
    
    def prepare_for_training(self, df: pd.DataFrame) -> tuple:
        """
        Prepare features and labels for model training.
        
        Args:
            df: DataFrame with features and labels
            
        Returns:
            Tuple of (X, y, feature_names)
        """
        # Get features
        feature_names = self.get_feature_names(df)
        
        # Drop rows with missing target
        if 'label_unhealthy' in df.columns:
            df = df.dropna(subset=['label_unhealthy'])
        
        # Drop rows with too many missing features
        df = df.dropna(subset=['AQI_prev1'], how='any')
        
        # Get X and y
        X = df[feature_names].copy()
        y = df['label_unhealthy'].copy() if 'label_unhealthy' in df.columns else None
        
        # Fill remaining NaN values
        X = X.fillna(X.median())
        
        return X, y, feature_names
    
    def create_features_from_dict(self, feature_dict: Dict) -> pd.DataFrame:
        """
        Create a single-row feature DataFrame from a dictionary.
        Useful for real-time prediction.
        
        Args:
            feature_dict: Dictionary with feature values
            
        Returns:
            Single-row DataFrame ready for prediction
        """
        df = pd.DataFrame([feature_dict])
        
        # Add derived features if base features are present
        if 'temp_max' in df.columns and 'wind_avg' in df.columns:
            df['temp_wind_ratio'] = df['temp_max'] / (df['wind_avg'] + 1)
        
        if 'wind_avg' in df.columns:
            df['is_stagnant'] = (df['wind_avg'] < 5).astype(int)
            df['wind_category'] = pd.cut(df['wind_avg'],
                                          bins=[-np.inf, 5, 10, 15, np.inf],
                                          labels=[0, 1, 2, 3]).astype(float)
        
        if 'precip' in df.columns:
            df['has_rain'] = (df['precip'] > 0.1).astype(int)
        
        if 'temp_max' in df.columns:
            df['temp_bin'] = pd.cut(df['temp_max'],
                                     bins=[-np.inf, 32, 50, 70, 90, np.inf],
                                     labels=[0, 1, 2, 3, 4]).astype(float)
        
        if 'rh_avg' in df.columns:
            df['humidity_high'] = (df['rh_avg'] > 70).astype(int)
        
        # Cyclical features
        if 'month' in df.columns:
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
            df['season'] = df['month'] % 12 // 3
        
        if 'day_of_week' in df.columns:
            df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
