import React, { useState } from 'react';
import { Send, Loader2, Bug, BookOpen, Wand2, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { queryAPI } from '../services/api';
import QueryResponse from '../components/QueryResponse';

const QUERY_TYPES = [
  { value: 'debug', label: 'Debug', icon: Bug, color: 'text-red-400' },
  { value: 'explain', label: 'Explain', icon: BookOpen, color: 'text-blue-400' },
  { value: 'generate', label: 'Generate', icon: Wand2, color: 'text-green-400' },
  { value: 'optimize', label: 'Optimize', icon: Zap, color: 'text-yellow-400' },
];

const LANGUAGES = [
  'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
  'go', 'rust', 'ruby', 'php', 'swift', 'kotlin',
];

function QueryPage() {
  const [formData, setFormData] = useState({
    question: '',
    code_snippet: '',
    language: 'python',
    error_message: '',
    query_type: 'debug',
  });
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.question.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      const result = await queryAPI.submit(formData);
      setResponse(result.data);

      if (result.data.status === 'completed') {
        toast.success('Response generated successfully!');
      } else if (result.data.status === 'failed') {
        toast.error('Query processing failed');
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to submit query';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Ask CodeMentor</h1>
        <p className="text-gray-500 mt-1">
          Get AI-powered help with debugging, explanations, and code generation
        </p>
      </div>

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Query Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            What do you need help with?
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {QUERY_TYPES.map(({ value, label, icon: Icon, color }) => (
              <button
                key={value}
                type="button"
                onClick={() => setFormData({ ...formData, query_type: value })}
                className={`flex items-center gap-2 p-3 rounded-lg border transition-all ${
                  formData.query_type === value
                    ? 'border-primary-500 bg-primary-500/10 text-white'
                    : 'border-dark-600 bg-dark-800 text-gray-400 hover:border-dark-500'
                }`}
              >
                <Icon className={`w-4 h-4 ${color}`} />
                <span className="text-sm font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Question */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            Your Question
          </label>
          <textarea
            className="input-field min-h-[100px] resize-y"
            placeholder="Describe your coding problem, question, or what you want to generate..."
            value={formData.question}
            onChange={(e) => setFormData({ ...formData, question: e.target.value })}
            required
          />
        </div>

        {/* Code Snippet */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">
            Code Snippet <span className="text-gray-600">(optional)</span>
          </label>
          <textarea
            className="input-field font-mono text-sm min-h-[150px] resize-y"
            placeholder="Paste your code here..."
            value={formData.code_snippet}
            onChange={(e) => setFormData({ ...formData, code_snippet: e.target.value })}
          />
        </div>

        {/* Language & Error */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Language
            </label>
            <select
              className="input-field"
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang} value={lang}>
                  {lang.charAt(0).toUpperCase() + lang.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Error Message <span className="text-gray-600">(optional)</span>
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g., IndexError: list index out of range"
              value={formData.error_message}
              onChange={(e) => setFormData({ ...formData, error_message: e.target.value })}
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full py-3 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Processing with Multi-Agent Pipeline...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Submit Query
            </>
          )}
        </button>
      </form>

      {/* Response */}
      {response && <QueryResponse response={response} />}
    </div>
  );
}

export default QueryPage;
