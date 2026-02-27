import React, { useState, useEffect, useRef } from 'react'
import MapView from './MapView'
import './main.css'

export default function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [focus, setFocus] = useState<{ lat: number | string; lon: number | string; zoom?: number } | null>(null)
  const [highlight, setHighlight] = useState<any | null>(null)
  const debounceRef = useRef<number | null>(null)
  const suggestionsRef = useRef<HTMLDivElement | null>(null)

  function handleInputChange(val: string) {
    setQuery(val)
    // Clear previous search result immediately when the user types a new query
    setResult(null)
    if (debounceRef.current) window.clearTimeout(debounceRef.current)
    if (!val || val.length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    debounceRef.current = window.setTimeout(async () => {
      try {
        const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=6&q=${encodeURIComponent(val)}`
        const res = await fetch(url)
        if (!res.ok) throw new Error('geocode error')
        const data = await res.json()
        setSuggestions(data || [])
        setShowSuggestions((data || []).length > 0)
      } catch (err) {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 300)
  }

  function formatSuggestion(s: any) {
    const addr = s?.address || {}
    const city = addr.city || addr.town || addr.village || ''
    const province = addr.state || addr.county || addr.region || addr.state_district || ''
    const country = addr.country || s?.country || ''
    const parts = [] as string[]
    if (city) parts.push(city)
    if (province && province !== city) parts.push(province)
    if (country && country !== province && country !== city) parts.push(country)
    if (parts.length) return parts.join(', ')
    const fallback = (s?.display_name || '').split(',').map((p: string) => p.trim()).filter(Boolean)
    return fallback.slice(0, 3).join(', ') || s?.display_name || ''
  }

  async function doSearch(city: string) {
    if (!city) return
    setLoading(true)
    setResult(null)
    try {
      // Try geocoding the city name first to get reliable coordinates
      try {
        const g = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(city)}`)
        if (g.ok) {
          const gd = await g.json()
          if (gd && gd.length > 0 && (gd[0].lat || gd[0].lon)) {
            const lat = Number(gd[0].lat)
            const lon = Number(gd[0].lon)
            setFocus({ lat, lon, zoom: 10 })
            await doSearchCoords(lat, lon)
            return
          }
        }
      } catch (ge) {
        // ignore geocode errors and fallback to text search
      }

      // Fallback: use text-based search on backend
      const res = await fetch(`/api/air-quality/${encodeURIComponent(city)}`)
      if (!res.ok) throw new Error(res.statusText)
      const data = await res.json()
      const iaqi = data?.iaqi || {}
      const temp = iaqi.t?.v ?? iaqi.temp?.v ?? null
      const humidity = iaqi.h?.v ?? iaqi.hum?.v ?? null
      // If backend returned coordinates, focus the map there
      let latFromData: number | null = null
      let lonFromData: number | null = null
      if (Array.isArray(data?.city?.geo) && data.city.geo.length >= 2) {
        latFromData = Number(data.city.geo[0])
        lonFromData = Number(data.city.geo[1])
      } else if (Array.isArray(data?.station?.geo) && data.station.geo.length >= 2) {
        latFromData = Number(data.station.geo[0])
        lonFromData = Number(data.station.geo[1])
      }

      const resObj = { aqi: data.aqi, temp: typeof temp === 'number' ? temp : null, humidity: typeof humidity === 'number' ? humidity : null, place: data?.city?.name ?? city }
      setResult(resObj)
      setHighlight(resObj)
      if (latFromData != null && lonFromData != null && !isNaN(latFromData) && !isNaN(lonFromData)) {
        setFocus({ lat: latFromData, lon: lonFromData, zoom: 10 })
      }
    } catch (err: any) {
      setResult({ place: `Error: ${err.message}` })
    } finally {
      setLoading(false)
    }
  }

  async function doSearchCoords(lat: number | string, lon: number | string) {
    if (lat == null || lon == null) return
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(`/api/air-quality-coords/${encodeURIComponent(lat)}/${encodeURIComponent(lon)}`)
      if (!res.ok) throw new Error(res.statusText)
      const data = await res.json()
      const iaqi = data?.iaqi || {}
      const temp = iaqi.t?.v ?? iaqi.temp?.v ?? null
      const humidity = iaqi.h?.v ?? iaqi.hum?.v ?? null
      const place = data?.city?.name || `${lat},${lon}`
      const resObj = { aqi: data.aqi, temp: typeof temp === 'number' ? temp : null, humidity: typeof humidity === 'number' ? humidity : null, place }
      setResult(resObj)
      setHighlight(resObj)
      // ensure map focuses on these coordinates
      const latn = Number(lat)
      const lonn = Number(lon)
      if (!isNaN(latn) && !isNaN(lonn)) setFocus({ lat: latn, lon: lonn, zoom: 10 })
    } catch (err: any) {
      setResult({ place: `Error: ${err.message}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="left-panel">
        <div className="left-top">
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
            <div>
              <div className="logo-title">Air Quality</div>
              <div className="logo-sub">Latest AQI readings</div>
            </div>
          </div>

          <div style={{ marginTop:14 }}>
            <div className="search-box">
              <div ref={suggestionsRef} style={{ width:'100%' }}>
                <input
                  className="search-input"
                  placeholder="Enter city name (e.g. Jakarta)"
                  value={query}
                  onChange={e => handleInputChange(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { doSearch(query); setShowSuggestions(false) } }}
                />

                {showSuggestions && suggestions.length > 0 && (
                  <div className="suggestions-list">
                    {suggestions.map((s: any, idx: number) => (
                      <div key={idx} className="suggestion-item" onMouseDown={() => {
                        const name = formatSuggestion(s)
                        setQuery(name)
                        setSuggestions([])
                        setShowSuggestions(false)
                        // Prefer using coordinates when available (more reliable)
                        if (s && (s.lat || s.lon)) {
                          const latn = Number(s.lat)
                          const lonn = Number(s.lon)
                          setFocus({ lat: latn, lon: lonn, zoom: 10 })
                          doSearchCoords(latn, lonn)
                        } else {
                          setFocus(null)
                          doSearch(name)
                        }
                      }}>
                        <div style={{ fontSize:13 }}>{formatSuggestion(s)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button className="search-btn" onClick={() => { doSearch(query); setShowSuggestions(false) }} disabled={loading}>{loading ? 'Searching...' : 'Search'}</button>
            </div>

            <div className="search-result" style={{ marginTop:12 }}>
              {result ? (
                <div>
                  <div style={{ fontSize:14, fontWeight:700 }}>{result.place}</div>
                  <div style={{ display:'flex', gap:8, marginTop:8 }}>
                    <div className="aqi-result-card">
                      <div className="aqi-label">AQI</div>
                      <div className="aqi-value">{result.aqi ?? 'N/A'}</div>
                    </div>
                    <div style={{ padding:10, borderRadius:8, background:'#e6f0ff', minWidth:100 }}>
                      <div style={{ fontSize:12, color:'#2459a8' }}>Temperature</div>
                      <div style={{ fontSize:18, fontWeight:800, color:'#08385f' }}>{result.temp != null ? `${result.temp} °C` : 'N/A'}</div>
                    </div>
                    <div style={{ padding:10, borderRadius:8, background:'#eaf7ea', minWidth:100 }}>
                      <div style={{ fontSize:12, color:'#1a7f2a' }}>Humidity</div>
                      <div style={{ fontSize:18, fontWeight:800, color:'#0b5b2a' }}>{result.humidity != null ? `${result.humidity} %` : 'N/A'}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ color:'var(--muted)', marginTop:8 }}>No data. Search for a city above.</div>
              )}
            </div>
          </div>
        </div>

        <div className="left-bottom">
          <div style={{ fontSize:13, color:'var(--muted)', marginBottom:8 }}>AQI Ranges</div>
          <div className="aqi-legend">
            <div className="legend-row"><span className="swatch aqi-good"/> <span className="legend-text">0 - 50 — Good</span></div>
            <div className="legend-row"><span className="swatch aqi-moderate"/> <span className="legend-text">51 - 100 — Moderate</span></div>
            <div className="legend-row"><span className="swatch aqi-unhealthy"/> <span className="legend-text">101 - 150 — Unhealthy for sensitive groups</span></div>
            <div className="legend-row"><span className="swatch aqi-veryunhealthy"/> <span className="legend-text">151 - 200 — Unhealthy</span></div>
            <div className="legend-row"><span className="swatch aqi-hazardous"/> <span className="legend-text">201+ — Very Unhealthy / Hazardous</span></div>
          </div>
          <div style={{ marginTop:10 }}>
            <div className="share-row">Updated just now · <span style={{ color:'var(--muted)', marginLeft:8 }}>Refresh</span></div>
          </div>
        </div>
      </aside>

      <main className="map-wrapper">
        <div className="globe-frame">
            <div className="map-inner">
            <MapView focus={focus ?? undefined} highlight={highlight ?? undefined} />
          </div>
        </div>

        <div className="map-overlay-info">3D GLOBE &nbsp; IQ AIR MAP</div>

        <div className="map-controls">
          <button>＋</button>
          <button>−</button>
        </div>
      </main>
    </div>
  )
}
