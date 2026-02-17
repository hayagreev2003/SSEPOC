"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useStreamingChat } from "../hooks/useStreamingChat";

export default function ManualSSEChat() {
  const [input, setInput] = useState("");
  const { messages, isStreaming, error, sendMessage, stop } =
    useStreamingChat("http://localhost:8000/chat");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
    setInput("");
  }

  return (
    <div className="space-y-6">
      <div
        ref={scrollRef}
        className="min-h-[200px] max-h-[500px] overflow-y-auto rounded-lg border border-zinc-200 bg-white p-4 text-zinc-800 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
      >
        {messages.length === 0 && !error && (
          <span className="text-zinc-400">
            Conversation will appear here...
          </span>
        )}
        {messages.map((m) => (
          <div key={m.id} className="mb-4 last:mb-0">
            <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              {m.role === "user" ? "You" : "Assistant"}
            </div>
            <div>
              {m.content ? (
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-4">{children}</p>,
                    ul: ({ children }) => (
                      <ul className="mb-4 list-disc pl-5">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="mb-4 list-decimal pl-5">{children}</ol>
                    ),
                    li: ({ children }) => (
                      <li className="mb-2">{children}</li>
                    ),
                    code: ({ children }) => (
                      <code className="bg-zinc-100 px-2 py-1 rounded dark:bg-zinc-800">
                        {children}
                      </code>
                    ),
                  }}
                >
                  {m.content}
                </ReactMarkdown>
              ) : null}
            </div>
          </div>
        ))}
        {isStreaming && (
          <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-zinc-400" />
        )}
        {error && <p className="text-red-500">Error: {error}</p>}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 rounded-lg border border-zinc-300 px-4 py-2 text-zinc-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={stop}
            className="rounded-lg bg-red-600 px-6 py-2 font-medium text-white transition-colors hover:bg-red-700"
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            className="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        )}
      </form>
    </div>
  );
}
