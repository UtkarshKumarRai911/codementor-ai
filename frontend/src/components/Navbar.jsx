import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Brain, History, LogOut, Code2 } from 'lucide-react';

function Navbar({ onLogout }) {
  const location = useLocation();

  const isActive = (path) =>
    location.pathname === path
      ? 'text-primary-400 border-b-2 border-primary-400'
      : 'text-gray-400 hover:text-gray-200';

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-900/95 backdrop-blur-sm border-b border-dark-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <Brain className="w-8 h-8 text-primary-500 group-hover:text-primary-400 transition-colors" />
            <span className="text-xl font-bold text-white">
              Code<span className="text-primary-400">Mentor</span> AI
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className={`flex items-center gap-1.5 pb-0.5 text-sm font-medium transition-colors ${isActive('/')}`}
            >
              <Code2 className="w-4 h-4" />
              Query
            </Link>
            <Link
              to="/history"
              className={`flex items-center gap-1.5 pb-0.5 text-sm font-medium transition-colors ${isActive('/history')}`}
            >
              <History className="w-4 h-4" />
              History
            </Link>
            <button
              onClick={onLogout}
              className="flex items-center gap-1.5 text-sm font-medium text-gray-400 hover:text-red-400 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
