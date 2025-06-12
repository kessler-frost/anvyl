import { useEffect, useState } from 'react'
import axios from 'axios'

interface Host {
  id: number
  name: string
  ip: string
  agents_installed: boolean
}

export default function App() {
  const [hosts, setHosts] = useState<Host[]>([])

  useEffect(() => {
    axios.get<Host[]>('/api/hosts').then(res => setHosts(res.data))
  }, [])

  return (
    <div className="p-6">
      <button
        onClick={() => window.open('/docs', '_blank')}
        className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow-sm transition-colors mb-6"
      >
        Open API Documentation
      </button>
      <h1 className="text-3xl font-bold mb-4">Sindri Dashboard</h1>
      {hosts.map(host => (
        <div key={host.id} className="bg-gray-800 p-4 rounded-xl mb-6 shadow">
          <h2 className="text-xl font-semibold">{host.name} ({host.ip})</h2>
          {host.agents_installed ? (
            <iframe
              src={`http://${host.ip}:8888`}
              className="w-full h-80 mt-4 border border-gray-700"
              title={`Logs for ${host.name}`}
            ></iframe>
          ) : (
            <p className="text-gray-400">Agents not installed</p>
          )}
        </div>
      ))}
    </div>
  )
}