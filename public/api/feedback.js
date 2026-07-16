// Принимает голос модератора по посту (👍/👎) и пишет его в Redis.
// HSET feedback:up / feedback:down <id> <json-метаданные поста>
// При смене голоса удаляет запись из противоположного хэша.

const { createClient } = require("redis");

let clientPromise;
function getClient() {
  if (!clientPromise) {
    const client = createClient({ url: process.env.REDIS_URL });
    client.on("error", (e) => console.error("Redis error:", e));
    clientPromise = client.connect().then(() => client);
  }
  return clientPromise;
}

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ error: "method not allowed" });
    return;
  }

  if (!process.env.REDIS_URL) {
    res.status(500).json({ error: "Redis not configured" });
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

  const meta = {
    id,
    text: typeof body.text === "string" ? body.text.slice(0, 500) : "",
    category: body.category || "",
    theme: body.theme || "",
    sentiment: body.sentiment || "",
    severity: body.severity || null,
    platform: body.platform || "",
    voted_at: new Date().toISOString(),
  };

  try {
    const client = await getClient();
    const target = verdict === "up" ? "feedback:up" : "feedback:down";
    const other = verdict === "up" ? "feedback:down" : "feedback:up";
    await client.hSet(target, id, JSON.stringify(meta));
    await client.hDel(other, id);
    res.status(200).json({ ok: true });
  } catch (e) {
    res.status(502).json({ error: String(e) });
  }
};
