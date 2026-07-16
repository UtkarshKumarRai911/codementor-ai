import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Bug, BookOpen, Wand2, Zap, ChevronLeft, ChevronRight, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';
import { queryAPI } from '../services/api';
import QueryResponse from '../components/QueryResponse';

const TYPE_ICONS = {
  debug: { icon: Bug, color: 'text-red-400', bg: 'bg-red-400/10' },
  explain: { icon: BookOpen, color: 'text-blue-400', bg: 'bg-blue-400/10' },
  generate: { icon: Wand2, color: 'text-green-400', bg: 'bg-green-400/10' },
  optimize: { icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
};

function HistoryPage() {
  const navigate = useNavigate();
  const [queries, setQueries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedQuery, setSelectedQuery] = useState(null);

  useEffect(() => {
    fetchHistory();
    fetchStats();
  }, [page]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await queryAPI.getHistory(page);
      setQueries(response.data.results || []);
      const count = response.data.count || 0;
      setTotalPages(Math.ceil(count / 20));
    } catch (error) {
      toast.error('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await queryAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleQueryClick = async (queryId) => {
    try {
      const response = await queryAPI.getDetail(queryId);
      setSelectedQuery(response.data);
    } catch (error) {
      toast.error('Failed to load query details');
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Query History</h1>
        <p className="text-gray-500 mt-1">View your past queries and responses</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-4 h-4 text-primary-400" />
              <span className="text-xs text-gray-500">Total Queries</span>
            </div>
            <p className="text-2xl font-bold text-white">{stats.total_queries}</p>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-green-400" />
              <span className="text-xs text-gray-500">Completed</span>
            </div>
            <p className="text-2xl font-bold text-green-400">{stats.completed_queries}</p>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-gray-500">Avg Time</span>
            </div>
            <p className="text-2xl font-bold text-white">
              {stats.avg_processing_time_ms ? `${Math.round(stats.avg_processing_time_ms)}ms` : 'N/A'}
            </p>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-500">Avg Rating</span>
            </div>
            <p className="text-2xl font-bold text-white">
              {stats.avg_feedback_rating ? `${stats.avg_feedback_rating.toFixed(1)}/5` : 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Query List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Query List */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto"></div>
              <p className="text-gray-500 mt-4">Loading history...</p>
            </div>
          ) : queries.length === 0 ? (
            <div className="text-center py-12 card">
              <p className="text-gray-500">No queries yet. Start by asking a question!</p>
            </div>
          ) : (
            queries.map((query) => {
              const typeConfig = TYPE_ICONS[query.query_type] || TYPE_ICONS.debug;
              const Icon = typeConfig.icon;

              return (
                <button
                  key={query.id}
                  onClick={() => handleQueryClick(query.id)}
                  className={`w-full text-left card-hover p-4 ${
                    selectedQuery?.id === query.id ? 'border-primary-500' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${typeConfig.bg}`}>
                      <Icon className={`w-4 h-4 ${typeConfig.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {query.question}
                      </p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-gray-500">{query.language}</span>
                        <span className={`text-xs ${
                          query.status === 'completed' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {query.status}
                        </span>
                        {query.processing_time_ms && (
                          <span className="text-xs text-gray-600">{query.processing_time_ms}ms</span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-gray-600 whitespace-nowrap">
                      {formatDate(query.created_at)}
                    </span>
                  </div>
                </button>
              );
            })
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-4">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="btn-secondary p-2 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-400">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="btn-secondary p-2 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Right: Selected Query Detail */}
        <div className="hidden lg:block">
          {selectedQuery ? (
            <div className="sticky top-20">
              <QueryResponse response={selectedQuery} />
            </div>
          ) : (
            <div className="card flex items-center justify-center min-h-[300px]">
              <p className="text-gray-500 text-center">
                Select a query to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HistoryPage;
