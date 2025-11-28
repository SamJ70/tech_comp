// frontend/src/App.jsx (COMPLETE REPLACEMENT)
import React, { useState, useEffect } from 'react';
import { 
  Camera, Globe, TrendingUp, Download, RefreshCw, AlertCircle, 
  CheckCircle, Info, Shield, Clock, Activity, BarChart3, AlertTriangle,
  Calendar, Target, Database, FileWarning
} from 'lucide-react';
import "./styles/global.css";

const API_URL = 'http://localhost:8000';

export default function TechComparisonApp() {
  const [mode, setMode] = useState('comparison'); // 'comparison' or 'single'
  const [countries, setCountries] = useState([]);
  const [domains, setDomains] = useState([]);
  
  // Comparison mode state
  const [selectedCountry1, setSelectedCountry1] = useState('');
  const [selectedCountry2, setSelectedCountry2] = useState('');
  
  // Single country mode state
  const [selectedCountry, setSelectedCountry] = useState('');
  
  // Common state
  const [selectedDomain, setSelectedDomain] = useState('');
  const [timeRange, setTimeRange] = useState(null);
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCountries();
    fetchDomains();
  }, []);

  useEffect(() => {
    let interval;
    if (taskId && status?.status !== 'completed' && status?.status !== 'failed') {
      interval = setInterval(() => checkStatus(taskId), 2000);
    }
    return () => clearInterval(interval);
  }, [taskId, status]);

  const fetchCountries = async () => {
    try {
      const response = await fetch(`${API_URL}/countries`);
      const data = await response.json();
      setCountries(data.countries);
    } catch (err) {
      console.error('Failed to fetch countries:', err);
    }
  };

  const fetchDomains = async () => {
    try {
      const response = await fetch(`${API_URL}/domains`);
      const data = await response.json();
      setDomains(data.domains);
    } catch (err) {
      console.error('Failed to fetch domains:', err);
    }
  };

  const handleCompare = async () => {
    if (mode === 'comparison') {
      if (!selectedCountry1 || !selectedCountry2 || !selectedDomain) {
        setError('Please select two countries and a domain');
        return;
      }
    } else {
      if (!selectedCountry || !selectedDomain) {
        setError('Please select a country and a domain');
        return;
      }
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setStatus(null);

    try {
      const endpoint = mode === 'comparison' ? '/compare' : '/analyze-country';
      const body = mode === 'comparison' 
        ? {
            country1: selectedCountry1,
            country2: selectedCountry2,
            domain: selectedDomain,
            include_charts: true,
            detail_level: 'standard',
            time_range: timeRange
          }
        : {
            country: selectedCountry,
            domain: selectedDomain,
            time_range: timeRange,
            include_dual_use: true,
            include_chronology: true
          };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) throw new Error('Failed to start analysis');

      const data = await response.json();
      setTaskId(data.task_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const checkStatus = async (id) => {
    try {
      const response = await fetch(`${API_URL}/status/${id}`);
      const data = await response.json();
      setStatus(data);

      if (data.status === 'completed') {
        setResults(data.results);
        setLoading(false);
      } else if (data.status === 'failed') {
        setError(data.message);
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to check status:', err);
    }
  };

  const downloadReport = (filename) => {
    window.open(`${API_URL}/download/${filename}`, '_blank');
  };

  const getRiskColor = (riskLevel) => {
    const colors = {
      'LOW': 'text-green-700 bg-green-50 border-green-200',
      'MODERATE': 'text-yellow-700 bg-yellow-50 border-yellow-200',
      'HIGH': 'text-orange-700 bg-orange-50 border-orange-200',
      'CRITICAL': 'text-red-700 bg-red-50 border-red-200'
    };
    return colors[riskLevel] || 'text-gray-700 bg-gray-50 border-gray-200';
  };

  const getComplianceColor = (status) => {
    const colors = {
      'COMPLIANT': 'text-green-700 bg-green-50',
      'MONITORING_REQUIRED': 'text-yellow-700 bg-yellow-50',
      'NON_COMPLIANT': 'text-orange-700 bg-orange-50',
      'CRITICAL_VIOLATION': 'text-red-700 bg-red-50'
    };
    return colors[status] || 'text-gray-700 bg-gray-50';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-2 border-indigo-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-10 h-10 text-indigo-600" />
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Tech Intelligence Platform
                </h1>
                <p className="text-sm text-gray-600">Dual-Use Monitoring & Technology Tracking System</p>
              </div>
            </div>
            <Database className="w-8 h-8 text-indigo-600" />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Mode Selector */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-center space-x-4 mb-6">
            <button
              onClick={() => { setMode('comparison'); setResults(null); }}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                mode === 'comparison'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <BarChart3 className="w-5 h-5 inline mr-2" />
              Compare Countries
            </button>
            <button
              onClick={() => { setMode('single'); setResults(null); }}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                mode === 'single'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Target className="w-5 h-5 inline mr-2" />
              Analyze Single Country
            </button>
          </div>

          {/* Selection Panel */}
          <div className="space-y-6">
            {mode === 'comparison' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Country
                  </label>
                  <select
                    value={selectedCountry1}
                    onChange={(e) => setSelectedCountry1(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={loading}
                  >
                    <option value="">Select country...</option>
                    {countries.map((country) => (
                      <option key={country.code + '1'} value={country.name}>
                        {country.flag} {country.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Second Country
                  </label>
                  <select
                    value={selectedCountry2}
                    onChange={(e) => setSelectedCountry2(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={loading}
                  >
                    <option value="">Select country...</option>
                    {countries.map((country) => (
                      <option key={country.code + '2'} value={country.name}>
                        {country.flag} {country.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Country
                </label>
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={loading}
                >
                  <option value="">Select country...</option>
                  {countries.map((country) => (
                    <option key={country.code} value={country.name}>
                      {country.flag} {country.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Technology Domain
                </label>
                <select
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={loading}
                >
                  <option value="">Select domain...</option>
                  {domains.map((domain) => (
                    <option key={domain.id} value={domain.id}>
                      {domain.icon} {domain.name}
                      {domain.dual_use_risk === 'HIGH' && ' ⚠️'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Clock className="w-4 h-4 inline mr-1" />
                  Time Range
                </label>
                <select
                  value={timeRange || ''}
                  onChange={(e) => setTimeRange(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={loading}
                >
                  <option value="">All time</option>
                  <option value="1">Last year</option>
                  <option value="2">Last 2 years</option>
                  <option value="5">Last 5 years</option>
                  <option value="10">Last 10 years</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleCompare}
              disabled={loading || (mode === 'comparison' ? (!selectedCountry1 || !selectedCountry2 || !selectedDomain) : (!selectedCountry || !selectedDomain))}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center shadow-lg"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Activity className="w-5 h-5 mr-2" />
                  Start {mode === 'comparison' ? 'Comparison' : 'Analysis'}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-lg shadow">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700 font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* Status Progress */}
        {status && status.status !== 'completed' && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Analysis Progress</h3>
              <span className="text-sm font-bold text-indigo-600">{status.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 mb-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-4 rounded-full transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 flex items-center">
              <Activity className="w-4 h-4 mr-2 animate-pulse text-indigo-600" />
              {status.message}
            </p>
          </div>
        )}

        {/* Results - Single Country Mode */}
        {results && results.type === 'single_country' && (
          <div className="space-y-6">
            {/* Dual-Use Analysis */}
            {results.dual_use_analysis && (
              <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-indigo-500">
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <Shield className="w-6 h-6 mr-2 text-indigo-600" />
                  Dual-Use Technology Analysis
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className={`p-4 rounded-lg border-2 ${getRiskColor(results.dual_use_analysis.risk_level)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">Risk Level</span>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <p className="text-2xl font-bold">{results.dual_use_analysis.risk_level}</p>
                    <p className="text-sm mt-1">{results.dual_use_analysis.risk_description}</p>
                  </div>

                  <div className={`p-4 rounded-lg ${getComplianceColor(results.dual_use_analysis.compliance_status)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">Compliance Status</span>
                      <CheckCircle className="w-5 h-5" />
                    </div>
                    <p className="text-xl font-bold">{results.dual_use_analysis.compliance_status.replace(/_/g, ' ')}</p>
                    <p className="text-sm mt-1">{results.dual_use_analysis.compliance_notes}</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <h4 className="font-semibold text-gray-800 mb-2">Wassenaar Category</h4>
                  <p className="text-gray-700">{results.dual_use_analysis.wassenaar_category}</p>
                  <p className="text-sm text-gray-600 mt-2">
                    <strong>Safe Limit:</strong> {results.dual_use_analysis.safe_limit}
                  </p>
                </div>

                {results.dual_use_analysis.military_indicators?.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-4 mb-4 border border-red-200">
                    <h4 className="font-semibold text-red-800 mb-3 flex items-center">
                      <FileWarning className="w-5 h-5 mr-2" />
                      Military Application Indicators ({results.dual_use_analysis.military_indicators.length})
                    </h4>
                    <div className="space-y-2">
                      {results.dual_use_analysis.military_indicators.slice(0, 5).map((indicator, idx) => (
                        <div key={idx} className="bg-white p-3 rounded border-l-4 border-red-400">
                          <p className="font-medium text-red-900">{indicator.indicator}</p>
                          <p className="text-sm text-gray-600 mt-1">{indicator.context}</p>
                          <span className={`text-xs px-2 py-1 rounded mt-2 inline-block ${
                            indicator.severity === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                          }`}>
                            {indicator.severity} SEVERITY
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {results.dual_use_analysis.recommendations?.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <h4 className="font-semibold text-blue-800 mb-2">Recommendations</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-700">
                      {results.dual_use_analysis.recommendations.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Chronological Analysis */}
            {results.chronological_analysis && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <Calendar className="w-6 h-6 mr-2 text-purple-600" />
                  Chronological Progress Timeline
                </h3>

                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 mb-6">
                  <p className="text-gray-700">{results.chronological_analysis.summary}</p>
                </div>

                {/* Trends */}
                {results.chronological_analysis.trends && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-blue-50 rounded-lg p-4 text-center">
                      <p className="text-sm text-gray-600 mb-1">Activity Trend</p>
                      <p className="text-xl font-bold text-blue-700">
                        {results.chronological_analysis.trends.activity_trend.replace(/_/g, ' ').toUpperCase()}
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4 text-center">
                      <p className="text-sm text-gray-600 mb-1">Acceleration</p>
                      <p className="text-xl font-bold text-green-700">
                        {results.chronological_analysis.trends.acceleration.replace(/_/g, ' ').toUpperCase()}
                      </p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4 text-center">
                      <p className="text-sm text-gray-600 mb-1">Most Active Year</p>
                      <p className="text-xl font-bold text-purple-700">
                        {results.chronological_analysis.trends.most_active_year}
                      </p>
                    </div>
                  </div>
                )}

                {/* Timeline */}
                <div className="space-y-4">
                  {results.chronological_analysis.timeline?.slice(0, 10).map((item, idx) => (
                    <div key={idx} className="border-l-4 border-indigo-500 pl-4 py-2 bg-gray-50 rounded-r-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-lg font-bold text-gray-800">{item.year}</h4>
                        <span className="text-sm bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full">
                          {item.total_events} events
                        </span>
                      </div>
                      {item.highlights?.length > 0 && (
                        <div className="mb-2">
                          <p className="text-sm font-semibold text-gray-700 mb-1">Key Highlights:</p>
                          {item.highlights.map((highlight, hidx) => (
                            <p key={hidx} className="text-sm text-gray-600 ml-2">• {highlight.slice(0, 200)}...</p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Results - Comparison Mode */}
        {results && results.type === 'comparison' && (
          <div className="space-y-6">
            {/* Comparison Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {results.countries.map((country) => (
                <div key={country} className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                    <Globe className="w-5 h-5 mr-2 text-indigo-600" />
                    {country}
                  </h3>
                  <div className="prose prose-sm text-gray-600 mb-4">
                    {results.summary[country]}
                  </div>

                  {/* Dual-Use Summary */}
                  {results.dual_use_analysis && results.dual_use_analysis[country] && (
                    <div className={`mt-4 p-3 rounded-lg border ${getRiskColor(results.dual_use_analysis[country].risk_level)}`}>
                      <p className="font-semibold mb-1">Dual-Use Risk: {results.dual_use_analysis[country].risk_level}</p>
                      <p className="text-xs">{results.dual_use_analysis[country].compliance_status.replace(/_/g, ' ')}</p>
                    </div>
                  )}

                  {/* Trend Summary */}
                  {results.trends && results.trends[country] && (
                    <div className="mt-4 p-3 bg-purple-50 rounded-lg">
                      <p className="text-sm font-semibold text-purple-800">
                        Activity Trend: {results.trends[country].activity_trend.replace(/_/g, ' ').toUpperCase()}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Overall Analysis */}
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl shadow-lg p-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                <CheckCircle className="w-6 h-6 mr-2 text-green-600" />
                Overall Conclusion
              </h3>
              <div className="prose prose-lg text-gray-700 whitespace-pre-line">
                {results.overall_analysis}
              </div>
            </div>

            {/* Download Button */}
            {results.document && (
              <div className="bg-white rounded-xl shadow-lg p-6 text-center">
                <button
                  onClick={() => downloadReport(results.document.filename)}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200 inline-flex items-center shadow-lg"
                >
                  <Download className="w-5 h-5 mr-2" />
                  Download Full Report (DOCX)
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t-2 border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-600">
          <p className="mb-2">Tech Intelligence Platform v3.0 | Dual-Use Monitoring & Technology Tracking</p>
          <p className="text-xs">Based on Wassenaar Arrangement Guidelines • Real-time Data Analysis • Chronological Tracking</p>
        </div>
      </footer>
    </div>
  );
}