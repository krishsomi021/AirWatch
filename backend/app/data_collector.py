"""Data collection from EPA, AirNow, and NWS APIs."""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DataCollector:
    """Collect air quality and weather data from public APIs."""
    
    def __init__(self, airnow_api_key: str = "", nws_user_agent: str = ""):
        """Initialize data collector with API credentials."""
        self.airnow_api_key = airnow_api_key
        self.nws_user_agent = nws_user_agent
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': nws_user_agent})
    
    def fetch_airnow_forecast(self, zip_code: str = "08901") -> Dict:
        """
        Fetch AirNow forecast for a ZIP code.
        
        Args:
            zip_code: New Jersey ZIP code
            
        Returns:
            Dictionary with AQI forecast data
        """
        if not self.airnow_api_key:
            logger.warning("No AirNow API key provided")
            return {}
        
        url = "https://www.airnowapi.org/aq/forecast/zipCode/"
        params = {
            'format': 'application/json',
            'zipCode': zip_code,
            'distance': 25,
            'API_KEY': self.airnow_api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract PM2.5 data
            pm25_data = [d for d in data if d.get('ParameterName') == 'PM2.5']
            if pm25_data:
                return pm25_data[0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching AirNow data: {e}")
            return {}
    
    def fetch_airnow_current(self, zip_code: str = "08901") -> Dict:
        """
        Fetch current AQI observation for a ZIP code.
        
        Args:
            zip_code: New Jersey ZIP code
            
        Returns:
            Dictionary with current AQI data
        """
        if not self.airnow_api_key:
            return {}
        
        url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
        params = {
            'format': 'application/json',
            'zipCode': zip_code,
            'distance': 25,
            'API_KEY': self.airnow_api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract PM2.5 data
            pm25_data = [d for d in data if d.get('ParameterName') == 'PM2.5']
            if pm25_data:
                return pm25_data[0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching current AirNow data: {e}")
            return {}
    
    def fetch_nws_forecast(self, lat: float = 40.4862, lon: float = -74.4518) -> Dict:
        """
        Fetch NWS weather forecast for coordinates (default: New Brunswick, NJ).
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with weather forecast
        """
        try:
            # Get forecast URL for this location
            points_url = f"https://api.weather.gov/points/{lat},{lon}"
            response = self.session.get(points_url, timeout=10)
            response.raise_for_status()
            forecast_url = response.json()['properties']['forecast']
            
            # Get actual forecast
            response = self.session.get(forecast_url, timeout=10)
            response.raise_for_status()
            forecast_data = response.json()
            
            periods = forecast_data['properties']['periods']
            
            # Extract tomorrow's forecast (typically periods[2-3])
            tomorrow_periods = [p for p in periods[:4] 
                              if 'tomorrow' in p.get('name', '').lower()]
            
            if tomorrow_periods:
                return self._parse_nws_period(tomorrow_periods[0])
            elif len(periods) >= 2:
                return self._parse_nws_period(periods[1])
            
            return {}
        except Exception as e:
            logger.error(f"Error fetching NWS forecast: {e}")
            return {}
    
    def _parse_nws_period(self, period: Dict) -> Dict:
        """Parse NWS forecast period into features."""
        return {
            'temp': period.get('temperature', 70),
            'wind_speed': self._extract_wind_speed(period.get('windSpeed', '0 mph')),
            'wind_direction': period.get('windDirection', 'N'),
            'short_forecast': period.get('shortForecast', ''),
            'precip_prob': period.get('probabilityOfPrecipitation', {}).get('value', 0) or 0
        }
    
    def _extract_wind_speed(self, wind_str: str) -> float:
        """Extract numeric wind speed from NWS string like '10 to 15 mph'."""
        try:
            # Take the average if range given
            parts = wind_str.lower().replace('mph', '').strip().split('to')
            if len(parts) == 2:
                return (float(parts[0]) + float(parts[1])) / 2
            return float(parts[0])
        except:
            return 5.0  # Default
    
    def download_epa_historical(self, 
                                year: int, 
                                state: str = "New Jersey",
                                output_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Download EPA historical daily AQI data.
        Note: This requires manual download from EPA website.
        Placeholder for automated downloading if API becomes available.
        
        Args:
            year: Year to download
            state: State name
            output_path: Where to save the data
            
        Returns:
            DataFrame with historical AQI data
        """
        logger.info(f"EPA historical data for {year} should be manually downloaded from:")
        logger.info("https://www.epa.gov/outdoor-air-quality-data/download-daily-data")
        logger.info("Select: Daily Data, PM2.5, New Jersey, and download CSV")
        
        # If file exists, load it
        if output_path and output_path.exists():
            return pd.read_csv(output_path)
        
        return pd.DataFrame()
    
    def fetch_openaq_data(self, 
                          location_id: Optional[int] = None,
                          days_back: int = 7) -> pd.DataFrame:
        """
        Fetch air quality data from OpenAQ API.
        
        Args:
            location_id: Specific location ID (optional)
            days_back: Number of days to fetch
            
        Returns:
            DataFrame with PM2.5 measurements
        """
        url = "https://api.openaq.org/v2/measurements"
        
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'country': 'US',
            'parameter': 'pm25',
            'date_from': date_from,
            'date_to': date_to,
            'limit': 1000
        }
        
        if location_id:
            params['location_id'] = location_id
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'results' in data:
                df = pd.DataFrame(data['results'])
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching OpenAQ data: {e}")
            return pd.DataFrame()


# NJ ZIP code to coordinates mapping (sample)
NJ_ZIP_COORDS = {
    '08901': (40.4862, -74.4518),  # New Brunswick
    '07960': (40.7968, -74.4821),  # Morristown
    '08540': (40.3573, -74.6672),  # Princeton
    '07302': (40.7178, -74.0431),  # Jersey City
    '08002': (39.8654, -75.0357),  # Cherry Hill
}


def get_coordinates_for_zip(zip_code: str) -> tuple:
    """Get lat/lon for a NJ ZIP code."""
    return NJ_ZIP_COORDS.get(zip_code, (40.0583, -74.4057))  # Default: NJ center
