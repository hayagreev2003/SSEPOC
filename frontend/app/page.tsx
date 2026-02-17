"use client";

import { useState } from "react";
import ManualSSEChat from "./components/ManualSSEChat";
import AIChatTab from "./components/AIChatTab";

const tabs = ["Manual SSE", "AI SDK"] as const;
type Tab = (typeof tabs)[number];

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("Manual SSE");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 p-8 font-sans dark:bg-black">
      <main className="w-full max-w-2xl space-y-6">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          SSE Streaming Chat
        </h1>

        <div className="inline-flex rounded-full bg-zinc-200 p-1 dark:bg-zinc-800">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "bg-white text-zinc-900 shadow-sm dark:bg-zinc-700 dark:text-zinc-100"
                  : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "Manual SSE" ? <ManualSSEChat /> : <AIChatTab />}
      </main>
    </div>
  );
}
