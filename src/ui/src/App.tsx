import { useState, useEffect } from 'react'
import './App.css'

interface Host {
  id: number
  name: string
  ip_address: string
  status: string
  created_at: string
}

function App() {
  const [hosts, setHosts] = useState<Host[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHosts()
  }, [])

  const fetchHosts = async () => {
    try {
      const response = await fetch('/api/hosts')
      const data = await response.json()
      setHosts(data)
    } catch (error) {
      console.error('Error fetching hosts:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-4">Anvyl Dashboard</h1>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading hosts...</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {hosts.map((host) => (
              <div key={host.id} className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-2">{host.name}</h3>
                <p className="text-gray-600 mb-2">IP: {host.ip_address}</p>
                <span className={`inline-block px-2 py-1 rounded-full text-sm ${
                  host.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {host.status}
                </span>
                <p className="text-sm text-gray-500 mt-2">
                  Added: {new Date(host.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default App