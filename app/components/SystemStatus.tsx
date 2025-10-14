"use client";

import { useEffect, useState } from "react";
import { Activity, Server, Clock, Database, ChevronUp, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SystemStats {
  total_queries: number;
  avg_response_time: number;
  uptime_seconds: number;
  vector_store_info: {
    total_vectors: number;
    model: string;
  };
}

interface QueryHistoryItem {
  query: string;
  answer: string;
  timestamp: number;
  confidence: number;
}

export function SystemStatus() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch("http://localhost:8000/api/stats"),
        fetch("http://localhost:8000/api/history?limit=5"),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (historyRes.ok) {
        const data = await historyRes.json();
        setHistory(data.history);
      }
    } catch (error) {
      console.error("Failed to fetch system status:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="mb-4 w-80 bg-black/80 backdrop-blur-md border border-white/10 rounded-2xl p-4 shadow-2xl text-white overflow-hidden"
          >
            <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-2">
              <h3 className="font-semibold flex items-center gap-2">
                <Activity className="w-4 h-4 text-green-400" />
                System Status
              </h3>
              <span className="text-xs text-green-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                Online
              </span>
            </div>

            {loading ? (
              <div className="space-y-2 animate-pulse">
                <div className="h-4 bg-white/10 rounded w-3/4" />
                <div className="h-4 bg-white/10 rounded w-1/2" />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-white/5 p-2 rounded-lg">
                    <div className="text-gray-400 mb-1 flex items-center gap-1">
                      <Server className="w-3 h-3" /> Queries
                    </div>
                    <div className="font-mono text-lg">{stats?.total_queries}</div>
                  </div>
                  <div className="bg-white/5 p-2 rounded-lg">
                    <div className="text-gray-400 mb-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Uptime
                    </div>
                    <div className="font-mono text-lg">
                      {stats ? formatUptime(stats.uptime_seconds) : "-"}
                    </div>
                  </div>
                  <div className="bg-white/5 p-2 rounded-lg col-span-2">
                    <div className="text-gray-400 mb-1 flex items-center gap-1">
                      <Database className="w-3 h-3" /> Vectors
                    </div>
                    <div className="font-mono">
                      {stats?.vector_store_info.total_vectors} documents indexed
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                    Recent Activity
                  </h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1 scrollbar-thin">
                    {history.length === 0 ? (
                      <div className="text-xs text-gray-500 italic">No recent queries</div>
                    ) : (
                      history.map((item, i) => (
                        <div key={i} className="text-xs bg-white/5 p-2 rounded border-l-2 border-blue-500">
                          <div className="font-medium truncate text-blue-200">
                            {item.query}
                          </div>
                          <div className="text-gray-400 truncate mt-0.5">
                            {item.answer}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-black/80 backdrop-blur-md border border-white/10 text-white p-3 rounded-full shadow-lg hover:bg-white/10 transition-colors group"
      >
        {isOpen ? (
          <ChevronDown className="w-5 h-5" />
        ) : (
          <Activity className="w-5 h-5 group-hover:text-green-400 transition-colors" />
        )}
      </button>
    </div>
  );
}
