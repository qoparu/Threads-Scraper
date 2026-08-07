// Принимает голос модератора по посту (👍/👎) и пишет его в Postgres (Neon).
// Одна строка на пост: смена голоса просто перезаписывает verdict/voted_at.

const { neon } = require("@neondatabase/serverless");

let sqlPromise;
function getSql() {
  if (!sqlPromise) {
    sqlPromise = Promise.resolve(neon(process.env.DATABASE_URL));
  }
  return sqlPromise;
}

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ error: "method not allowed" });
    return;
  }

  if (!process.env.DATABASE_URL) {
    res.status(500).json({ error: "Postgres not configured" });
    return;
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = {}; }
  }
  body = body || {};

  const { id, verdict } = body;
  if (!id || (verdict !== "up" && verdict !== "down")) {
    res.status(400).json({ error: "id and verdict ('up'|'down') are required" });
    return;
  }

  const text = typeof body.text === "string" ? body.text.slice(0, 500) : "";
  const category = body.category || "";
  const theme = body.theme || "";
  const sentiment = body.sentiment || "";
  const severity = body.severity == null || body.severity === "" ? null : Number(body.severity);
  const platform = body.platform || "";

  try {
    const sql = await getSql();
    await sql`
      CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        verdict TEXT NOT NULL,
        text TEXT,
        category TEXT,
        theme TEXT,
        sentiment TEXT,
        severity INTEGER,
        platform TEXT,
        voted_at TIMESTAMPTZ NOT NULL DEFAULT now()
      )
    `;
    await sql`
      INSERT INTO feedback (id, verdict, text, category, theme, sentiment, severity, platform, voted_at)
      VALUES (${id}, ${verdict}, ${text}, ${category}, ${theme}, ${sentiment}, ${severity}, ${platform}, now())
      ON CONFLICT (id) DO UPDATE SET
        verdict = EXCLUDED.verdict, text = EXCLUDED.text, category = EXCLUDED.category,
        theme = EXCLUDED.theme, sentiment = EXCLUDED.sentiment, severity = EXCLUDED.severity,
        platform = EXCLUDED.platform, voted_at = EXCLUDED.voted_at
    `;
    res.status(200).json({ ok: true });
  } catch (e) {
    res.status(502).json({ error: String(e) });
  }
};
