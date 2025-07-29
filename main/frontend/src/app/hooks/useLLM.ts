"use client";

import { useState } from "react";

export function useLLM(baseUrl: string = "http://192.168.50.143:8000") {
  const [llmAnswer, setLlmAnswer] = useState("");
  const [devAnswer, setDevAnswer] = useState<string | null>(null);
  const [loadingAnswer, setLoadingAnswer] = useState(false);

  const askLLM = async (question: string) => {
    setLlmAnswer("");
    try {
      const res = await fetch(`${baseUrl}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setLlmAnswer(data.answer);
    } catch (err) {
      console.error("Failed to query LLM:", err);
      setLlmAnswer("❌ Failed to get a response.");
    }
  };

  const askDevAssistant = async (question: string, metadata?: any) => {
    if (!question.trim()) return;
    setLoadingAnswer(true);
    setDevAnswer("");

    try {
      const res = await fetch(`${baseUrl}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, metadata }),
      });
      const data = await res.json();
      setDevAnswer(data.answer);
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
