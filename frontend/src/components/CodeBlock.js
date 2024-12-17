import React from 'react';
import { Copy, Check } from 'lucide-react';

function CodeBlock({ children, className }) {
  const [copied, setCopied] = React.useState(false);
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className={className}>
        <button
          onClick={handleCopy}
          className="absolute right-2 top-2 p-2 rounded-lg bg-gray-600 hover:bg-gray-500 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-400" />
          ) : (
            <Copy className="w-4 h-4 text-gray-300" />
          )}
        </button>
        <code>{children}</code>
      </pre>
    </div>
  );
}

export default CodeBlock;