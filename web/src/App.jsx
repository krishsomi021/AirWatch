import { useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

function App() {
  const [zipCode, setZipCode] = useState('')
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPrediction = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const zip = zipCode || '08901'
      const response = await fetch(`${API_BASE_URL}/predict?zip_code=${zip}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch prediction')
      }
      
      const data = await response.json()
      setPrediction(data)
    } catch (err) {
      setError(err.message || 'An error occurred while fetching the prediction')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    fetchPrediction()
  }

  const getConfidenceClass = (confidence) => {
    const conf = confidence.toLowerCase()
    if (conf === 'high') return 'confidence-high'
    if (conf === 'medium') return 'confidence-medium'
    return 'confidence-low'
  }

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>
            <span>🌤️</span>
            AirWatch
          </h1>
          <p>Next-Day Air Quality Forecast for New Jersey</p>
        </div>

        <form onSubmit={handleSubmit} className="search-section">
          <div className="search-box">
            <input
              type="text"
              className="input-field"
              placeholder="Enter NJ ZIP Code (e.g., 08901)"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value)}
              pattern="[0-9]{5}"
              maxLength="5"
            />
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Check Air Quality'}
            </button>
          </div>
          <p className="help-text">
            Leave blank for New Brunswick, NJ or enter any NJ ZIP code
          </p>
        </form>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing air quality data...</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {prediction && !loading && (
          <div className="result-card">
            <div className="result-header">
              <div className="result-date">
                Forecast for {new Date(prediction.date).toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </div>
              <div className="result-location">
                Location: {prediction.location}
              </div>
            </div>

            <div style={{ textAlign: 'center' }}>
              <div className={`result-badge ${prediction.classification === 'Safe' ? 'badge-safe' : 'badge-unhealthy'}`}>
                {prediction.classification === 'Safe' ? '✓ Safe' : '⚠ Unhealthy'}
              </div>
            </div>

            <div className="result-probability">
              Probability of Unhealthy Air: {(prediction.prob_unhealthy * 100).toFixed(1)}%
            </div>

            <div className="result-category">
              {prediction.aqi_category}
            </div>

            <div className="confidence-indicator">
              <span className={`confidence-dot ${getConfidenceClass(prediction.confidence)}`}></span>
              <span>Confidence: {prediction.confidence}</span>
            </div>

            {prediction.top_factors && prediction.top_factors.length > 0 && (
              <div className="factors-section">
                <div className="factors-title">Contributing Factors:</div>
                <ul className="factors-list">
                  {prediction.top_factors.map((factor, index) => (
                    <li key={index} className="factor-item">
                      <span className="factor-icon">•</span>
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="legend">
          <div className="legend-title">Understanding the Forecast:</div>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#d4edda' }}></div>
              <span><strong>Safe:</strong> Air quality is Good to Moderate (AQI ≤ 100)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#f8d7da' }}></div>
              <span><strong>Unhealthy:</strong> Unhealthy for Sensitive Groups or worse (AQI ≥ 101)</span>
            </div>
          </div>
        </div>

        <div className="footer">
          <p>Data sources: EPA, AirNow, National Weather Service</p>
          <p>Model uses PM₂.₅ levels and weather forecasts for prediction</p>
        </div>
      </div>
    </div>
  )
}

export default App
