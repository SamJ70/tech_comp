// frontend/src/App.jsx (THEMED BRIEFING UI — WITH MULTILINGUAL SEARCH & EXTRA SOURCES)
import React, { useState, useEffect } from "react";
import { Shield, Database, Download, RefreshCw } from "lucide-react";
import "./styles/global.css";

const API_URL = "http://localhost:8000";

function RiskPill({ level }) {
  if (!level) return <span className="risk-low">UNKNOWN</span>;
  const map = {
    LOW: "risk-low",
    MODERATE: "risk-moderate",
    HIGH: "risk-high",
    CRITICAL: "risk-critical"
  };
  return <span className={map[level] || "risk-moderate"}>{level}</span>;
}

function SeverityBar({ score }) {
  const pct = Math.max(0, Math.min(100, score || 0));
  return (
    <div style={{ width: "100%" }}>
      <div className="sev-bar">
        <div className="sev-fill" style={{ width: `${pct}%` }} />
      </div>
      <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 6 }}>{pct}%</div>
    </div>
  );
}

export default function App() {
  const [countries, setCountries] = useState([]);
  const [domains, setDomains] = useState([]);
  const [mode, setMode] = useState("comparison");
  const [selectedCountry1, setSelectedCountry1] = useState("");
  const [selectedCountry2, setSelectedCountry2] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("");
  const [selectedDomain, setSelectedDomain] = useState("");
  const [customDomain, setCustomDomain] = useState(""); // multilingual free-text domain override
  const [extraSourcesText, setExtraSourcesText] = useState(""); // user-supplied extra sources (one per line)
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
    let i;
    if (taskId && (!status || (status && status.status !== "completed"))) {
      i = setInterval(() => checkStatus(taskId), 2000);
    }
    return () => clearInterval(i);
  }, [taskId, status]);

  async function fetchCountries() {
    try {
      const r = await fetch(`${API_URL}/countries`);
      const d = await r.json();
      setCountries(d.countries || []);
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchDomains() {
    try {
      const r = await fetch(`${API_URL}/domains`);
      const d = await r.json();
      setDomains(d.domains || []);
    } catch (e) {
      console.error(e);
    }
  }

  function _parseExtraSources(text) {
    if (!text) return [];
    return text.split("\n").map(s => s.trim()).filter(Boolean);
  }

  async function startAnalysis() {
    setError(null);
    setLoading(true);
    setResults(null);
    try {
      // prefer customDomain (multilingual free-text) if provided
      const domainToUse = (customDomain && customDomain.trim()) ? customDomain.trim() : (selectedDomain || "");
      if (mode === "comparison") {
        if (!selectedCountry1 || !selectedCountry2 || !domainToUse) {
          setError("Please select two countries and a domain (or provide custom domain)");
          setLoading(false);
          return;
        }
      } else {
        if (!selectedCountry || !domainToUse) {
          setError("Please select a country and a domain (or provide custom domain)");
          setLoading(false);
          return;
        }
      }

      const payloadExtraSources = _parseExtraSources(extraSourcesText);

      const endpoint = mode === "comparison" ? "/compare" : "/analyze-country";
      const body = mode === "comparison"
        ? {
            country1: selectedCountry1,
            country2: selectedCountry2,
            // core domain field must be set (we set it to domainToUse)
            domain: domainToUse,
            // optional override
            ...(customDomain && customDomain.trim() ? { custom_domain: customDomain.trim() } : {}),
            extra_sources: payloadExtraSources,
            include_charts: true,
            detail_level: "standard",
            time_range: timeRange
          }
        : {
            country: selectedCountry,
            domain: domainToUse,
            ...(customDomain && customDomain.trim() ? { custom_domain: customDomain.trim() } : {}),
            extra_sources: payloadExtraSources,
            time_range: timeRange,
            include_dual_use: true,
            include_chronology: true
          };

      const r = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || "Failed to begin analysis");
      }
      const j = await r.json();
      setTaskId(j.task_id);
      setStatus({ status: "started", progress: 0, message: "Queued" });
    } catch (e) {
      setError(String(e));
      setLoading(false);
    }
  }

  async function checkStatus(id) {
    try {
      const r = await fetch(`${API_URL}/status/${id}`);
      const j = await r.json();
      setStatus(j);
      if (j.status === "completed") {
        setResults(j.results);
        setLoading(false);
      } else if (j.status === "failed") {
        setError(j.message || "failed");
        setLoading(false);
      }
    } catch (e) {
      console.error(e);
    }
  }

  function downloadReport(f) {
    window.open(`${API_URL}/download/${f}`, "_blank");
  }

  return (
    <div style={{ padding: 24 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{ width: 56, height: 56, borderRadius: 10, background: "linear-gradient(90deg,var(--accent),var(--accent-2))", display: "flex", alignItems: "center", justifyContent: "center", marginRight: 12 }}>
            <Shield style={{ color: "#031122" }} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, color: "#fff" }}>Strategic Tech Tracker</h1>
            <div style={{ color: "var(--muted)", fontSize: 13 }}>Dual-use intelligence briefs — chronological & risk insights</div>
          </div>
        </div>
        <div>
          <Database style={{ color: "white" }} />
        </div>
      </header>

      {error && (
        <div style={{
          marginTop: 12,
          marginBottom: 12,
          padding: 12,
          borderRadius: 8,
          background: "linear-gradient(90deg, rgba(239,68,68,0.08), rgba(245,158,11,0.04))",
          border: "1px solid rgba(239,68,68,0.12)",
          color: "#ffe6e6"
        }}>
          <strong style={{ marginRight: 8 }}>Error: </strong>
          <span style={{ color: "var(--muted)" }}>{String(error)}</span>
        </div>
      )}

      <section className="brief-card" style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
          <button onClick={() => setMode("comparison")} style={{ padding: "8px 12px", borderRadius: 8, background: mode === "comparison" ? "var(--accent)" : "transparent", color: mode === "comparison" ? "#031122" : "var(--muted)" }}>Compare</button>
          <button onClick={() => setMode("single")} style={{ padding: "8px 12px", borderRadius: 8, background: mode === "single" ? "var(--accent)" : "transparent", color: mode === "single" ? "#031122" : "var(--muted)" }}>Single</button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px,1fr))", gap: 12 }}>
          {mode === "comparison" ? (
            <>
              <select value={selectedCountry1} onChange={(e) => setSelectedCountry1(e.target.value)}>
                <option value="">First Country</option>
                {countries.map(c => <option value={c.name} key={c.code}>{c.flag} {c.name}</option>)}
              </select>
              <select value={selectedCountry2} onChange={(e) => setSelectedCountry2(e.target.value)}>
                <option value="">Second Country</option>
                {countries.map(c => <option value={c.name} key={c.code}>{c.flag} {c.name}</option>)}
              </select>
            </>
          ) : (
            <select value={selectedCountry} onChange={(e) => setSelectedCountry(e.target.value)}>
              <option value="">Select Country</option>
              {countries.map(c => <option value={c.name} key={c.code}>{c.flag} {c.name}</option>)}
            </select>
          )}

          <select value={selectedDomain} onChange={(e) => setSelectedDomain(e.target.value)}>
            <option value="">Select Domain</option>
            {domains.map(d => <option value={d.id} key={d.id}>{d.icon} {d.name}</option>)}
          </select>

          <input
            value={customDomain}
            onChange={(e) => setCustomDomain(e.target.value)}
            placeholder="Or type domain (any language) — e.g., 'ロボット' or '机器人' or 'robotics'"
            style={{ padding: "10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.06)", background: "transparent", color: "#e6eef8" }}
          />

          <select value={timeRange || ""} onChange={(e) => setTimeRange(e.target.value ? parseInt(e.target.value) : null)}>
            <option value="">All time</option>
            <option value="1">Last year</option>
            <option value="2">Last 2 years</option>
            <option value="5">Last 5 years</option>
          </select>

          <div>
            <button onClick={startAnalysis} disabled={loading} style={{ padding: "10px 14px", background: "linear-gradient(90deg,var(--accent),var(--accent-2))", borderRadius: 8, color: "#031122", fontWeight: 700 }}>
              {loading ? (<><RefreshCw /> Running...</>) : "Run"}
            </button>
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <label style={{ color: "var(--muted)", fontSize: 13 }}>Additional sources (one per line — URLs or text). These will be included in the report.</label>
          <textarea
            value={extraSourcesText}
            onChange={(e) => setExtraSourcesText(e.target.value)}
            placeholder="https://example.com/article1
https://another.source/article2
or plain text describing the source"
            rows={4}
            style={{ width: "100%", marginTop: 8, padding: 10, borderRadius: 8, border: "1px solid rgba(255,255,255,0.04)", background: "transparent", color: "#e6eef8" }}
          />
        </div>
      </section>

      {results && results.type === "single_country" && (
        <section className="brief-card" style={{ marginBottom: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <div>
              <h2 style={{ margin: 0 }}>{results.country}</h2>
              <div style={{ color: "var(--muted)" }}>{results.domain}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ marginBottom: 6 }}>Risk</div>
              <RiskPill level={results.dual_use_analysis?.risk_level} />
              <div style={{ marginTop: 8, color: "var(--muted)", fontSize: 12 }}>{results.dual_use_analysis?.compliance_status}</div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 12, marginTop: 12 }}>
            <div>
              <h3 style={{ color: "#fff" }}>Dual-Use Category Breakdown</h3>
              <div style={{ display: "grid", gap: 8 }}>
                {results.dual_use_analysis?.category_breakdown && Object.entries(results.dual_use_analysis.category_breakdown.scores || {}).slice(0,12).map(([cat, sc]) => (
                  <div key={cat} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 160, color: "var(--muted)" }}>{cat}</div>
                    <div style={{ flex: 1 }}><SeverityBar score={Math.round(sc*10)} /></div>
                    <div style={{ width: 48, textAlign: "right", color: "var(--muted)" }}>{Math.round(sc*10)}%</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 style={{ color: "#fff" }}>Top Matches</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {results.dual_use_analysis && Object.entries(results.dual_use_analysis.category_breakdown.top_matches || {}).slice(0,6).map(([cat, matches]) => (
                  <div key={cat} style={{ background: "rgba(255,255,255,0.02)", padding: 8, borderRadius: 8 }}>
                    <div style={{ fontWeight: 800 }}>{cat} ({matches.length})</div>
                    <div style={{ color: "var(--muted)", fontSize: 13 }}>{matches.slice(0,3).map(m => m.title || m.matched_keyword).join(" • ")}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <h3 style={{ color: "#fff" }}>Recommendations</h3>
            <ul style={{ color: "var(--muted)" }}>
              {results.dual_use_analysis.recommendations && results.dual_use_analysis.recommendations.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>

          <div style={{ marginTop: 12 }}>
            {results.document && <button onClick={() => downloadReport(results.document.filename)} style={{ padding: "8px 12px", borderRadius: 8, background: "var(--accent)", color: "#031122", fontWeight: 700 }}><Download /> Download DOCX</button>}
          </div>
        </section>
      )}

      {results && results.type === "comparison" && (
        <section className="brief-card">
          <h2>Comparison — Quick Brief</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 12 }}>
            {results.countries.map(country => (
              <div key={country} style={{ background: "transparent", padding: 12, borderRadius: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <div style={{ fontWeight: 800 }}>{country}</div>
                  <RiskPill level={results.dual_use_analysis?.[country]?.risk_level} />
                </div>
                <div style={{ color: "var(--muted)", marginTop: 8 }}>{results.summary?.[country]?.slice(0,300)}</div>
                <div style={{ marginTop: 8 }}>
                  <h4 style={{ margin: 0 }}>Top categories</h4>
                  {results.dual_use_analysis?.[country]?.category_breakdown && Object.entries(results.dual_use_analysis[country].category_breakdown.scores || {}).slice(0,6).map(([cat, sc]) => (
                    <div key={cat} style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 6 }}>
                      <div style={{ width: 4, height: 28, background: "linear-gradient(90deg,var(--accent),var(--accent-2))", borderRadius: 2 }} />
                      <div style={{ color: "var(--muted)" }}>{cat}</div>
                      <div style={{ marginLeft: "auto", color: "var(--muted)" }}>{Math.round(sc*10)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 12 }}>
            {results.document && <button onClick={() => downloadReport(results.document.filename)} style={{ padding: "8px 12px", borderRadius: 8, background: "linear-gradient(90deg,var(--accent),var(--accent-2))", color: "#031122", fontWeight: 700 }}><Download /> Download DOCX</button>}
          </div>
        </section>
      )}
    </div>
  );
}
