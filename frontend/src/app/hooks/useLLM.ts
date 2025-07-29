"use client";

import { useState } from "react";

export function useLLM(baseUrl: string = "http://192.168.50.143:8000") {
  const [llmAnswer, setLlmAnswer] = useState("");
  const [devAnswer, setDevAnswer] = useState<string | null>(null);
  const [loadingAnswer, setLoadingAnswer] = useState(false);

  // Simple analytics question (polling)
  const askLLM = async (question: string) => {
    setLlmAnswer("");
    try {
      // 1. Enqueue task
      const res = await fetch(`${baseUrl}/llm/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const { task_id } = await res.json();

      // 2. Poll for result
      let result;
      while (true) {
        const poll = await fetch(`${baseUrl}/llm/result/${task_id}`);
        result = await poll.json();
        if (result.status === "done") break;
        await new Promise((r) => setTimeout(r, 1500));
      }

      setLlmAnswer(result.result);
    } catch (err) {
      console.error("Failed to query LLM:", err);
      setLlmAnswer("❌ Failed to get a response.");
    }
  };

  // Developer assistant (streaming)
  const askDevAssistant = async (question: string, metadata?: any) => {
    if (!question.trim()) return;
    setLoadingAnswer(true);
    setDevAnswer("");

    try {
      // 1. Enqueue
      const res = await fetch(`${baseUrl}/llm/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, metadata }),
      });
      const { task_id } = await res.json();

      // 2. Stream tokens
      const streamRes = await fetch(`${baseUrl}/llm/stream/${task_id}`);
      const reader = streamRes.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("Streaming not supported");

      let fullText = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        setDevAnswer(fullText);
      }
    } catch (err) {
      console.error("Failed to query LLM:", err);
      setDevAnswer("Error: Could not fetch answer.");
    } finally {
      setLoadingAnswer(false);
    }
  };

  return {
    llmAnswer,
    devAnswer,
    loadingAnswer,
    askLLM,
    askDevAssistant,
  };
}
