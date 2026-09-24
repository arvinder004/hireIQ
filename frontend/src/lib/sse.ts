const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function streamMessage(
  sessionId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onDone: (stage: number) => void
): Promise<void> {
  const res = await fetch(`${BASE}/api/v1/interview/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!res.ok || !res.body) throw new Error("Stream connection failed.");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(line.slice(6));
        if (data.error) throw new Error(`Server error: ${data.error}`);
        if (data.chunk !== undefined) onChunk(data.chunk);
        if (data.done) onDone(data.stage);
      } catch { /* skip malformed events */ }
    }
  }
}
