import React, { useState, useEffect } from 'react';
import { Camera, Globe, TrendingUp, Download, RefreshCw, AlertCircle, CheckCircle, Info } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function TechComparisonApp() {
  const [countries, setCountries] = useState([]);
  const [domains, setDomains] = useState([]);
  const [selectedCountry1, setSelectedCountry1] = useState('');
  const [selectedCountry2, setSelectedCountry2] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  // Fetch initial data
  useEffect(() => {
    fetchCountries();
    fetchDomains();
    fetchHistory();
  }, []);

  // Poll for status updates
  useEffect(() => {
    let interval;
    if (taskId && status?.status !== 'completed' && status?.status !== 'failed') {
      interval = setInterval(() => {
        checkStatus(taskId);
      }, 2000);
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

  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/history`);
      const data = await response.json();
      setHistory(data.history || []);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleCompare = async () => {
    if (!selectedCountry1 || !selectedCountry2 || !selectedDomain) {
      setError('Please select two countries and a domain');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    setStatus(null);

    try {
      const response = await fetch(`${API_URL}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country1: selectedCountry1,
          country2: selectedCountry2,
          domain: selectedDomain,
          include_charts: true,
          detail_level: 'standard'
        })
      });

      if (!response.ok) throw new Error('Failed to start comparison');

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
        fetchHistory();
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="w-10 h-10 text-indigo-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Tech Comparison Platform</h1>
                <p className="text-sm text-gray-600">AI-Powered Country Technology Analysis</p>
              </div>
            </div>
            <TrendingUp className="w-8 h-8 text-indigo-600" />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Selection Panel */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
            <Camera className="w-6 h-6 mr-2 text-indigo-600" />
            Compare Countries
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Country 1 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                First Country
              </label>
              <select
                value={selectedCountry1}
                onChange={(e) => setSelectedCountry1(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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

            {/* Country 2 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Second Country
              </label>
              <select
                value={selectedCountry2}
                onChange={(e) => setSelectedCountry2(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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

            {/* Domain */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Technology Domain
              </label>
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={loading}
              >
                <option value="">Select domain...</option>
                {domains.map((domain) => (
                  <option key={domain.id} value={domain.id}>
                    {domain.icon} {domain.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={handleCompare}
            disabled={loading || !selectedCountry1 || !selectedCountry2 || !selectedDomain}
            className="mt-6 w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center"
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <TrendingUp className="w-5 h-5 mr-2" />
                Start Comparison
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Status Progress */}
        {status && status.status !== 'completed' && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Analysis Progress</h3>
              <span className="text-sm text-gray-600">{status.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
              <div
                className="bg-indigo-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600">{status.message}</p>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {results.countries.map((country) => (
                <div key={country} className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                    <Globe className="w-5 h-5 mr-2 text-indigo-600" />
                    {country}
                  </h3>
                  <div className="prose prose-sm text-gray-600">
                    {results.summary[country]}
                  </div>
                </div>
              ))}
            </div>

            {/* Comparison Analysis */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Comparative Analysis</h3>
              <div className="space-y-4">
                {Object.entries(results.comparison).map(([category, analysis]) => (
                  <div key={category} className="border-l-4 border-indigo-500 pl-4">
                    <h4 className="font-semibold text-gray-800 mb-2 capitalize">
                      {category.replace(/_/g, ' ')}
                    </h4>
                    <p className="text-gray-600">{analysis}</p>
                  </div>
                ))}
              </div>
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

            {/* Data Quality */}
            {results.data_quality && (
              <div className="bg-yellow-50 rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                  <Info className="w-5 h-5 mr-2 text-yellow-600" />
                  Data Quality Assessment
                </h3>
                <div className="space-y-2">
                  <p className="text-sm text-gray-700">
                    <strong>Confidence Level:</strong> {results.data_quality.confidence?.toUpperCase()}
                  </p>
                  {results.data_quality.warnings?.length > 0 && (
                    <div className="text-sm text-gray-600">
                      <strong>Notes:</strong>
                      <ul className="list-disc list-inside mt-1">
                        {results.data_quality.warnings.map((warning, idx) => (
                          <li key={idx}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Download Button */}
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <button
                onClick={() => downloadReport(results.document.filename)}
                className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200 inline-flex items-center"
              >
                <Download className="w-5 h-5 mr-2" />
                Download Full Report (DOCX)
              </button>
            </div>
          </div>
        )}

        {/* History */}
        {history.length > 0 && !loading && !results && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Recent Comparisons</h3>
            <div className="space-y-2">
              {history.slice(0, 5).map((item) => (
                <div key={item.task_id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">
                    {item.task_id.split('_').slice(0, 2).join(' vs ')}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(item.completed_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-600">
          <p>Tech Comparison Platform v2.0 | Powered by AI & Multi-Source Data Analysis</p>
        </div>
      </footer>
    </div>
  );
}