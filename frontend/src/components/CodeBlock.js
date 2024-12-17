import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

const languageNames = {
  js: "JavaScript",
  jsx: "React JSX",
  ts: "TypeScript",
  tsx: "TypeScript JSX",
  py: "Python",
  bash: "Shell",
  sh: "Shell",
  json: "JSON",
  css: "CSS",
  scss: "SCSS",
  html: "HTML",
  xml: "XML",
  md: "Markdown",
  yaml: "YAML",
  yml: "YAML",
  sql: "SQL",
  java: "Java",
  cpp: "C++",
  c: "C",
  cs: "C#",
  go: "Go",
  rust: "Rust",
  swift: "Swift",
  kotlin: "Kotlin",
  php: "PHP",
  ruby: "Ruby",
  perl: "Perl",
  r: "R",
  matlab: "MATLAB",
  scala: "Scala",
  dart: "Dart",
  lua: "Lua",
  groovy: "Groovy",
  dockerfile: "Dockerfile",
  graphql: "GraphQL",
  haskell: "Haskell",
  txt: "Plain Text",
};

const customStyle = {
  ...oneDark,
  'pre[class*="language-"]': {
    ...oneDark['pre[class*="language-"]'],
    margin: 0,
    borderRadius: 0,
    background: "transparent",
  },
  'code[class*="language-"]': {
    ...oneDark['code[class*="language-"]'],
    fontFamily:
      'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    display: "block",
    padding: "1rem 1.5rem",
    width: "100%",
    boxSizing: "border-box",
    fontSize: "0.875rem",
    lineHeight: "1.5rem",
    tabSize: 2,
  },
  comment: {
    ...oneDark.comment,
    fontStyle: "italic",
  },
  keyword: {
    ...oneDark.keyword,
    color: "#c678dd",
  },
  string: {
    ...oneDark.string,
    color: "#98c379",
  },
  function: {
    ...oneDark.function,
    color: "#61afef",
  },
};

const CodeBlock = ({
  children,
  className,
  showLineNumbers = true,
  maxHeight = null,
}) => {
  const [copied, setCopied] = useState(false);
  const language = className?.replace(/^language-/, "") || "text";
  const displayName = languageNames[language] || language;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy code:", err);
    }
  };

  return (
    <div className="rounded-lg overflow-hidden border border-[#313244] my-4 bg-[#1e1e2e]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#181825] border-b border-[#313244]">
        <span className="text-xs text-[#6c7086] font-medium">
          {displayName}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-[#313244] rounded-md transition-colors duration-200"
          title={copied ? "Copied!" : "Copy code"}
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-400" />
          ) : (
            <Copy className="w-4 h-4 text-[#6c7086]" />
          )}
          <span className="text-[#6c7086]">{copied ? "Copied!" : "Copy"}</span>
        </button>
      </div>

      <div
        className="overflow-auto"
        style={maxHeight ? { maxHeight } : undefined}
      >
        <SyntaxHighlighter
          language={language}
          style={customStyle}
          customStyle={{
            margin: 0,
            background: "transparent",
          }}
          showLineNumbers={showLineNumbers}
          lineNumberStyle={{
            minWidth: "3em",
            paddingRight: "1em",
            textAlign: "right",
            userSelect: "none",
            opacity: 0.5,
            borderRight: "1px solid #313244",
            marginRight: "1em",
          }}
          wrapLongLines={true}
        >
          {children}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default CodeBlock;
