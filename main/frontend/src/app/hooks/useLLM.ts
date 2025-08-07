"use client";

import { useState } from "react";

export function useLLM(baseUrl: string = "http://192.168.50.143:8000") {
  const [llmAnswer, setLlmAnswer] = useState("");
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

  return {
    llmAnswer,
    loadingAnswer,
    askLLM
  };
}
