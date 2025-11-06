"""
ML Predictor - Advanced Machine Learning Models for Price Prediction
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import TimeSeriesSplit
    import xgboost as xgb
    import lightgbm as lgb
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn/xgboost/lightgbm not available. ML predictions disabled.")


class MLPredictor:
    """
    Advanced ML Predictor using ensemble methods

    Models:
    - XGBoost (gradient boosting)
    - LightGBM (fast gradient boosting)
    - Random Forest
    - Gradient Boosting

    Features:
    - Technical indicators
    - Volume patterns
    - Price momentum
    - Volatility metrics
    """

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.trained = False

        if SKLEARN_AVAILABLE:
            self._initialize_models()

        logger.info("✓ ML Predictor created")

    def _initialize_models(self):
        """Initialize ensemble of models"""
        self.models = {
            'xgboost': xgb.XGBRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            ),
            'lightgbm': lgb.LGBMRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                verbose=-1
            ),
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        }

        self.scalers = {
            name: StandardScaler() for name in self.models.keys()
        }

    def engineer_features(
        self,
        ohlcv: np.ndarray,
        lookback: int = 50
    ) -> np.ndarray:
        """
        Engineer features from OHLCV data

        Args:
            ohlcv: OHLCV data array [timestamp, open, high, low, close, volume]
            lookback: Lookback period for features

        Returns:
            Feature matrix
        """
        if len(ohlcv) < lookback:
            raise ValueError(f"Insufficient data: need {lookback}, got {len(ohlcv)}")

        closes = ohlcv[:, 4]  # Close prices
        highs = ohlcv[:, 2]   # High prices
        lows = ohlcv[:, 3]    # Low prices
        volumes = ohlcv[:, 5] # Volumes

        features = []

        # Price-based features
        features.append(self._returns(closes, 1))
        features.append(self._returns(closes, 5))
        features.append(self._returns(closes, 10))
        features.append(self._returns(closes, 20))

        # Momentum features
        features.append(self._rsi(closes, 14))
        features.append(self._macd(closes))

        # Volatility features
        features.append(self._volatility(closes, 20))
        features.append(self._atr(highs, lows, closes, 14))

        # Volume features
        features.append(self._volume_ratio(volumes, 20))

        # Trend features
        features.append(self._sma_ratio(closes, 20))
        features.append(self._sma_ratio(closes, 50))
        features.append(self._ema_ratio(closes, 12, 26))

        # Combine features
        feature_matrix = np.column_stack(features)

        # Store feature names for reference
        self.feature_names = [
            'returns_1d', 'returns_5d', 'returns_10d', 'returns_20d',
            'rsi_14', 'macd',
            'volatility_20', 'atr_14',
            'volume_ratio_20',
            'sma_ratio_20', 'sma_ratio_50', 'ema_ratio_12_26'
        ]

        return feature_matrix

    def _returns(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate returns over period"""
        returns = np.zeros(len(prices))
        returns[period:] = (prices[period:] / prices[:-period]) - 1
        return returns

    def _rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.zeros(len(prices))
        avg_losses = np.zeros(len(prices))

        avg_gains[period] = np.mean(gains[:period])
        avg_losses[period] = np.mean(losses[:period])

        for i in range(period + 1, len(prices)):
            avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
            avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period

        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _macd(self, prices: np.ndarray) -> np.ndarray:
        """Calculate MACD"""
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)
        return ema_12 - ema_26

    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        multiplier = 2 / (period + 1)

        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]

        return ema

    def _volatility(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate rolling volatility"""
        returns = self._returns(prices, 1)
        volatility = np.zeros(len(prices))

        for i in range(period, len(prices)):
            volatility[i] = np.std(returns[i-period:i])

        return volatility

    def _atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int
    ) -> np.ndarray:
        """Calculate Average True Range"""
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )

        atr = np.zeros(len(closes))
        atr[period] = np.mean(tr[:period])

        for i in range(period + 1, len(closes)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i-1]) / period

        return atr

    def _volume_ratio(self, volumes: np.ndarray, period: int) -> np.ndarray:
        """Calculate volume ratio vs moving average"""
        volume_sma = np.zeros(len(volumes))

        for i in range(period, len(volumes)):
            volume_sma[i] = np.mean(volumes[i-period:i])

        ratio = np.divide(
            volumes,
            volume_sma,
            where=volume_sma != 0,
            out=np.ones_like(volumes)
        )

        return ratio

    def _sma_ratio(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate price / SMA ratio"""
        sma = np.zeros(len(prices))

        for i in range(period, len(prices)):
            sma[i] = np.mean(prices[i-period:i])

        ratio = np.divide(
            prices,
            sma,
            where=sma != 0,
            out=np.ones_like(prices)
        )

        return ratio

    def _ema_ratio(
        self,
        prices: np.ndarray,
        fast_period: int,
        slow_period: int
    ) -> np.ndarray:
        """Calculate fast EMA / slow EMA ratio"""
        fast_ema = self._ema(prices, fast_period)
        slow_ema = self._ema(prices, slow_period)

        ratio = np.divide(
            fast_ema,
            slow_ema,
            where=slow_ema != 0,
            out=np.ones_like(prices)
        )

        return ratio

    async def train(
        self,
        ohlcv: np.ndarray,
        horizon: int = 1
    ) -> Dict[str, float]:
        """
        Train ensemble of models

        Args:
            ohlcv: Historical OHLCV data
            horizon: Prediction horizon (days ahead)

        Returns:
            Training metrics
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available")
            return {"error": "ML libraries not installed"}

        logger.info(f"Training ML models on {len(ohlcv)} samples...")

        # Engineer features
        X = self.engineer_features(ohlcv)

        # Create targets (future returns)
        closes = ohlcv[:, 4]
        y = np.zeros(len(closes))
        y[:-horizon] = (closes[horizon:] / closes[:-horizon]) - 1

        # Remove NaN values
        valid_idx = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[valid_idx]
        y = y[valid_idx]

        if len(X) < 100:
            logger.warning(f"Insufficient training data: {len(X)} samples")
            return {"error": "Insufficient data"}

        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=5)

        metrics = {}

        for name, model in self.models.items():
            try:
                # Scale features
                X_scaled = self.scalers[name].fit_transform(X)

                # Train on full data
                model.fit(X_scaled, y)

                # Cross-validation scores
                cv_scores = []
                for train_idx, val_idx in tscv.split(X_scaled):
                    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                    y_train, y_val = y[train_idx], y[val_idx]

                    model.fit(X_train, y_train)
                    score = model.score(X_val, y_val)
                    cv_scores.append(score)

                metrics[name] = {
                    'cv_score': np.mean(cv_scores),
                    'cv_std': np.std(cv_scores)
                }

                logger.info(f"✓ {name}: CV Score = {metrics[name]['cv_score']:.4f} ± {metrics[name]['cv_std']:.4f}")

            except Exception as e:
                logger.error(f"Error training {name}: {e}")
                metrics[name] = {'error': str(e)}

        self.trained = True
        logger.info("✓ ML models trained successfully")

        return metrics

    async def predict(
        self,
        ohlcv: np.ndarray,
        ensemble_method: str = 'mean'
    ) -> Dict[str, Any]:
        """
        Predict future price movement

        Args:
            ohlcv: Recent OHLCV data
            ensemble_method: 'mean', 'median', or 'weighted'

        Returns:
            Prediction dict with expected return and confidence
        """
        if not SKLEARN_AVAILABLE or not self.trained:
            logger.warning("Models not trained or libraries unavailable")
            return {
                "prediction": 0.0,
                "confidence": 0.0,
                "method": "untrained"
            }

        # Engineer features from recent data
        X = self.engineer_features(ohlcv)
        X_latest = X[-1:]  # Most recent features

        # Get predictions from each model
        predictions = {}

        for name, model in self.models.items():
            try:
                X_scaled = self.scalers[name].transform(X_latest)
                pred = model.predict(X_scaled)[0]
                predictions[name] = pred
            except Exception as e:
                logger.error(f"Error predicting with {name}: {e}")

        if not predictions:
            return {
                "prediction": 0.0,
                "confidence": 0.0,
                "method": "error"
            }

        # Ensemble predictions
        pred_values = list(predictions.values())

        if ensemble_method == 'mean':
            final_prediction = np.mean(pred_values)
        elif ensemble_method == 'median':
            final_prediction = np.median(pred_values)
        elif ensemble_method == 'weighted':
            # Weight by inverse variance (more consistent models get higher weight)
            weights = 1 / (np.std(pred_values) + 1e-10)
            final_prediction = np.average(pred_values, weights=weights)
        else:
            final_prediction = np.mean(pred_values)

        # Calculate confidence as inverse of prediction variance
        confidence = 1 / (np.std(pred_values) + 1e-10)
        confidence = min(confidence, 1.0)  # Cap at 1.0

        return {
            "prediction": float(final_prediction),
            "confidence": float(confidence),
            "individual_predictions": predictions,
            "method": ensemble_method,
            "timestamp": datetime.now().isoformat()
        }

    def get_feature_importance(self, model_name: str = 'xgboost') -> Dict[str, float]:
        """Get feature importance from a specific model"""
        if model_name not in self.models or not self.trained:
            return {}

        model = self.models[model_name]

        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            return dict(zip(self.feature_names, importances))

        return {}
