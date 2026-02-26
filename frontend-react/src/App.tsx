import React from 'react'
import MapView from './MapView'

export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#f3f5f9', padding: 24 }}>
      <div style={{ width: '90%', maxWidth: 1100, height: 640, boxShadow: '0 8px 24px rgba(0,0,0,0.08)', borderRadius: 12, overflow: 'hidden', background: '#ffffff' }}>
        <MapView />
      </div>
    </div>
  )
}
