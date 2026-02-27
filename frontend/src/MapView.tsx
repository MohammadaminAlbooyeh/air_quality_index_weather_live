import React, { useState, useRef, useEffect } from 'react'
import { MapContainer, TileLayer, useMapEvents, Marker, Popup } from 'react-leaflet'
import L, { LatLngExpression } from 'leaflet'

// Fix default icon paths for Vite bundling by importing images
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Fix default icon paths for Vite bundling
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow
})

function ClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onClick(e.latlng.lat, e.latlng.lng)
    }
  })
  return null
}

export default function MapView({ focus, highlight }: { focus?: { lat: number | string; lon: number | string; zoom?: number }, highlight?: { aqi?: number; temp?: number | null; humidity?: number | null; place?: string } }) {
  const center: LatLngExpression = [20.0, 0.0] // world view center
  const [info, setInfo] = useState<string>('Click anywhere on the map to fetch air quality data')
  const [marker, setMarker] = useState<{ lat: number; lng: number } | null>(null)
  const [detail, setDetail] = useState<{ aqi?: number; temp?: number | null; humidity?: number | null; place?: string } | null>(null)
  const markerRef = useRef<any>(null)
  const mapRef = useRef<any>(null)

  useEffect(() => {
    if (markerRef.current) {
      try {
        markerRef.current.openPopup()
      } catch (e) {
        // ignore if popup can't open yet
      }
    }
  }, [marker, info])

  useEffect(() => {
    if (!focus || !mapRef.current) return
    try {
      const latn = Number(focus.lat)
      const lonn = Number(focus.lon)
      if (!isNaN(latn) && !isNaN(lonn)) {
        mapRef.current.flyTo([latn, lonn], focus.zoom ?? 10, { duration: 0.9 })
        setMarker({ lat: latn, lng: lonn })
        if (highlight && (highlight.aqi || highlight.place)) {
          setInfo(`AQI: ${highlight.aqi ?? 'N/A'} — ${highlight.place ?? ''}`)
          setDetail(highlight)
        } else {
          setInfo(`Location: ${latn.toFixed(3)}, ${lonn.toFixed(3)}`)
        }
      }
    } catch (e) {
      // ignore
    }
  }, [focus, highlight])

  async function handleClick(lat: number, lng: number) {
    setInfo(`Fetching air quality data for ${lat.toFixed(2)}, ${lng.toFixed(2)}...`)
    setDetail(null)
    setMarker({ lat, lng })
    try {
      const res = await fetch(`/api/air-quality-coords/${lat}/${lng}`)
      if (!res.ok) throw new Error(res.statusText)
      const data = await res.json()
      const iaqi = data?.iaqi || {}
      const temp = iaqi.t?.v ?? iaqi.temp?.v ?? null
      const humidity = iaqi.h?.v ?? iaqi.hum?.v ?? null
      setInfo(`AQI: ${data.aqi} — Dominant pollutant: ${data.dominentpol}`)
      setDetail({ aqi: data.aqi, temp: typeof temp === 'number' ? temp : null, humidity: typeof humidity === 'number' ? humidity : null, place: data?.city?.name })
    } catch (err: any) {
      setInfo(`Failed to fetch air quality data: ${err.message}`)
    }
  }

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <MapContainer whenCreated={(m) => { mapRef.current = m }} center={center} zoom={2} style={{ height: '100%', width: '100%' }}>
        {/* Use a colorful basemap (CartoDB Voyager) for richer colors */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png"
          attribution='© CARTO, © OpenStreetMap contributors'
        />
        <ClickHandler onClick={handleClick} />
        {marker && (
          <Marker position={[marker.lat, marker.lng]} ref={markerRef}>
            <Popup>{info}</Popup>
          </Marker>
        )}
      </MapContainer>

      {/* When `focus` prop changes, pan/zoom and place a marker reliably */}
      
      {/* useEffect ensures side-effects run when focus/highlight change */}
      
      {null}

      <div style={{ position: 'absolute', bottom: 12, left: 12, background: 'rgba(255,255,255,0.95)', padding: '8px 12px', borderRadius: 6, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
        <strong>Info:</strong>
        <div style={{ marginTop: 4 }}>{info}</div>
      </div>

      {detail && (
        <div style={{ position: 'absolute', top: 24, right: 24, width: 360, maxWidth: '90%', background: '#fff', borderRadius: 12, boxShadow: '0 12px 40px rgba(0,0,0,0.12)', padding: 18, zIndex: 1000 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: 14, color: '#666' }}>{detail.place ?? 'Selected location'}</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>Air Quality</div>
            </div>
            <button onClick={() => setDetail(null)} style={{ border: 'none', background: 'transparent', fontSize: 18, cursor: 'pointer' }}>✕</button>
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 14 }}>
            <div style={{ flex: 1, padding: 12, borderRadius: 10, background: '#fcf7f0' }}>
              <div style={{ fontSize: 12, color: '#9a6b00' }}>AQI</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#5a3e00' }}>{detail.aqi ?? 'N/A'}</div>
            </div>
            <div style={{ flex: 1, padding: 12, borderRadius: 10, background: '#e6f0ff' }}>
              <div style={{ fontSize: 12, color: '#2459a8' }}>Temperature</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#08385f' }}>{detail.temp != null ? `${detail.temp} °C` : 'N/A'}</div>
            </div>
            <div style={{ flex: 1, padding: 12, borderRadius: 10, background: '#eaf7ea' }}>
              <div style={{ fontSize: 12, color: '#1a7f2a' }}>Humidity</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#0b5b2a' }}>{detail.humidity != null ? `${detail.humidity} %` : 'N/A'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
