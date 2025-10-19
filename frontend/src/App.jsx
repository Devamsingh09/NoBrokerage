import React, { useState } from "react";
import { searchQuery } from "./api";

function Message({ who, text }) {
  return (
    <div className={`message ${who === 'user' ? 'user' : 'bot'}`}>
      <div className="bubble">{text}</div>
    </div>
  );
}

function Card({ c }) {
  return (
    <div className="card">
      {c.floorPlanImage && <img src={c.floorPlanImage} alt="Floor Plan" className="floor-plan" />}
      <div className="card-title">{c.title}</div>
      <div className="muted">{c.city} {c.locality ? `• ${c.locality}` : ""}</div>
      <div className="muted">{c.bhk} {c.price ? `• ${c.price}` : ""} {c.possession ? `• ${c.possession}` : ""}</div>
      <div className="amen">{c.amenities}</div>
      <a className="cta" href={c.cta}>View</a>
    </div>
  );
}

export default function App(){
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const send = async () => {
    const q = input.trim();
    if (!q) return;
    setMessages(m => [...m, { who: 'user', text: q }]);
    setInput("");
    try {
      const r = await searchQuery(q);
      const summary = r.summary || "No result.";
      setMessages(m => [...m, { who: 'user', text: q }, { who: 'bot', text: summary, cards: r.cards }]);
    } catch (err) {
      setMessages(m => [...m, { who: 'user', text: q }, { who: 'bot', text: "Error: " + err.message }]);
    }
  };

  return (
    <div className="container">
      <h1>NoBrokerage — Chat Search</h1>
      <div className="chat" id="chat-window">
        {messages.map((m, i) => (
          <div key={i}>
            <Message who={m.who} text={m.text} />
            {m.who === 'bot' && m.cards && m.cards.length > 0 && (
              <div className="cards">
                {m.cards.map((c, idx) => <Card key={idx} c={c} />)}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="input-row">
        <input
          value={input}
          onChange={(e)=>setInput(e.target.value)}
          placeholder='e.g., "3BHK flat in Pune under ₹1.2 Cr"'
          onKeyDown={(e)=>{ if (e.key === "Enter") send(); }}
        />
        <button onClick={send}>Send</button>
      </div>
    </div>
  );
}
