// api.js

// The BASE URL is fetched from the VITE_API_URL environment variable.
// If it's not set (e.g., in development without a .env file), 
// it falls back to your deployed backend URL.
// IMPORTANT: For production, ensure VITE_API_URL is set 
// in your deployment platform's environment variables or .env.production file.
const BASE = import.meta.env.VITE_API_URL || "https://nobrokerage-uj95.onrender.com";

export async function searchQuery(q) {
  const res = await fetch(`${BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q })
  });
  
  if (!res.ok) {
    const txt = await res.text();
    // Use the error message from the API if available, otherwise a generic error
    throw new Error(txt || `API error: Failed to fetch ${BASE}/api/search`); 
  }
  
  return res.json();
}
