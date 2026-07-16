import React from 'react';
import { BookOpen, Code2, Lightbulb, Database } from 'lucide-react';
import CodeBlock from './CodeBlock';

function QueryResponse({ response }) {
  if (!response) return null;

  const { explanation, fixed_code, similar_problems, retrieved_context, processing_time_ms, model_used } = response;

  return (
    <div className="space-y-6 mt-8">
      {/* Metadata Bar */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        {processing_time_ms && (
          <span>Processed in {processing_time_ms}ms</span>
        )}
        {model_used && <span>Model: {model_used}</span>}
      </div>

      {/* Explanation */}
      {explanation && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="w-5 h-5 text-primary-400" />
            <h3 className="text-lg font-semibold text-white">Explanation</h3>
          </div>
          <div className="prose prose-invert prose-sm max-w-none">
            <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
              {explanation}
            </p>
          </div>
        </div>
      )}

      {/* Fixed/Generated Code */}
      {fixed_code && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Code2 className="w-5 h-5 text-green-400" />
            <h3 className="text-lg font-semibold text-white">Code Solution</h3>
          </div>
          <CodeBlock code={fixed_code} language={response.language || 'python'} />
        </div>
      )}

      {/* Similar Problems */}
      {similar_problems && similar_problems.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-yellow-400" />
            <h3 className="text-lg font-semibold text-white">Similar Problems</h3>
          </div>
          <ul className="space-y-3">
            {similar_problems.map((problem, index) => (
              <li key={index} className="flex items-start gap-3 p-3 bg-dark-900 rounded-lg">
                <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-primary-900 text-primary-300 text-xs font-bold">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-200">{problem.title}</p>
                  {problem.approach && (
                    <p className="text-xs text-gray-400 mt-1">{problem.approach}</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Retrieved Context */}
      {retrieved_context && retrieved_context.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">
              Retrieved Context
              <span className="text-sm font-normal text-gray-500 ml-2">
                ({retrieved_context.length} sources)
              </span>
            </h3>
          </div>
          <div className="space-y-3">
            {retrieved_context.map((ctx, index) => (
              <details
                key={index}
                className="group bg-dark-900 rounded-lg overflow-hidden"
              >
                <summary className="flex items-center gap-2 p-3 cursor-pointer hover:bg-dark-800 transition-colors">
                  <span className="text-sm text-gray-400">Source {index + 1}</span>
                  {ctx.source && (
                    <span className="text-xs text-gray-600">({ctx.source})</span>
                  )}
                </summary>
                <div className="px-3 pb-3">
                  <p className="text-xs text-gray-400 whitespace-pre-wrap">
                    {ctx.content?.substring(0, 500)}
                    {ctx.content?.length > 500 && '...'}
                  </p>
                </div>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QueryResponse;
