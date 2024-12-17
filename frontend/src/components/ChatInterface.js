import React, { useState, useRef, useEffect } from "react";
import { Send, Upload } from "lucide-react";

function ThinkingAnimation() {
  return (
    <div className="flex items-center space-x-2 p-4 bg-gray-800 rounded-lg">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
      </div>
    </div>
  );
}

function TypeWriter({ content, onComplete }) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  
  useEffect(() => {
    if (currentIndex < content.length) {
      const timer = setTimeout(() => {
        const charsPerFrame = 3;
        const nextIndex = Math.min(currentIndex + charsPerFrame, content.length);
        const nextChunk = content.slice(currentIndex, nextIndex);
        
        setDisplayedContent(prev => prev + nextChunk);
        setCurrentIndex(prev => prev + charsPerFrame);
      }, 6); 
      
      return () => clearTimeout(timer);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentIndex, content, onComplete]);

  return <p className="whitespace-pre-wrap">{displayedContent}</p>;
}

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const question = input.trim();
    setInput("");
    setLoading(true);

    setMessages((prev) => [...prev, 
      { type: "user", content: question },
      { type: "thinking" } // Add thinking message
    ]);

    try {
      const response = await fetch("http://localhost:1512/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();
      if (response.ok) {
        // Remove thinking message and add assistant response
        setMessages((prev) => [
          ...prev.filter(msg => msg.type !== "thinking"),
          {
            type: "assistant",
            content: data.answer,
            sources: data.sources,
            isTyping: true,
          },
        ]);
      } else {
        throw new Error(data.error || "Failed to get response");
      }
    } catch (error) {
      // Remove thinking message and add error
      setMessages((prev) => [
        ...prev.filter(msg => msg.type !== "thinking"),
        {
          type: "error",
          content: error.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setLoading(true);
    let successCount = 0;
    let errorCount = 0;

    try {
      // Process files in parallel using Promise.all
      await Promise.all(files.map(async (file) => {
        const formData = new FormData();
        formData.append("file", file);

        try {
          const response = await fetch("http://localhost:1512/api/upload", {
            method: "POST",
            body: formData,
          });

          const data = await response.json();
          if (response.ok) {
            successCount++;
            setMessages((prev) => [
              ...prev,
              {
                type: "system",
                content: `File uploaded: ${file.name}`,
              },
            ]);
          } else {
            errorCount++;
            throw new Error(data.error || "Failed to upload file");
          }
        } catch (error) {
          errorCount++;
          setMessages((prev) => [
            ...prev,
            {
              type: "error",
              content: `Error uploading ${file.name}: ${error.message}`,
            },
          ]);
        }
      }));

      // Add summary message
      if (files.length > 1) {
        setMessages((prev) => [
          ...prev,
          {
            type: successCount === files.length ? "system" : "error",
            content: `Upload complete: ${successCount} successful, ${errorCount} failed`,
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          type: "error",
          content: "Error uploading files: " + error.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 shadow p-4">
        <h1 className="text-xl font-bold text-white">Hiraku AI</h1>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`flex ${
              message.type === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.type === "thinking" ? (
              <ThinkingAnimation />
            ) : (
              <div
                className={`max-w-3xl p-4 rounded-lg ${
                  message.type === "user"
                    ? "bg-blue-600 text-white"
                    : message.type === "assistant"
                    ? "bg-gray-800 text-gray-100"
                    : message.type === "error"
                    ? "bg-red-900 text-red-100"
                    : "bg-gray-700 text-gray-100"
                }`}
              >
                {message.type === "assistant" && message.isTyping ? (
                  <TypeWriter 
                    content={message.content}
                    onComplete={() => {
                      setMessages(prev => 
                        prev.map((msg, i) => 
                          i === idx ? { ...msg, isTyping: false } : msg
                        )
                      );
                    }}
                  />
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
                
                {message.sources && !message.isTyping && (
                  <div className="mt-2 text-xs space-y-1">
                    <div className="text-gray-400 font-semibold">Sources:</div>
                    {message.sources.map((source, i) => (
                      <div key={i} className="text-gray-400">
                        • {source.source} (Similarity:{" "}
                        {(source.similarity * 100).toFixed(1)}%)
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="bg-gray-800 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={`p-2 text-gray-400 hover:text-gray-200 ${
                loading ? "opacity-50 cursor-not-allowed" : ""
              }`}
              disabled={loading}
            >
              <Upload className="w-5 h-5" />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
              accept=".pdf,.txt,.csv,.doc,.docx,.md,.json"
              multiple
            />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={loading ? "Hiraku is thinking..." : "Ask any question..."}
              className="flex-1 p-2 border rounded-lg bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2 text-blue-400 hover:text-blue-300 disabled:text-gray-600"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
