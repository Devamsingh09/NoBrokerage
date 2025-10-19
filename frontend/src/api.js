const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function searchQuery(q) {
  const res = await fetch(`${BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q })
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "API error");
  }
  return res.json();
}
