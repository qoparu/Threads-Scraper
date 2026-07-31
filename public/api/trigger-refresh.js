// Публичная кнопка «Обновить сейчас» на дашборде. Не гоняет скрапер сам —
// у Vercel serverless функций нет времени на 20-30 минутный Playwright-прогон.
// Вместо этого дёргает GitHub Actions (workflow_dispatch) — тот же пайплайн,
// что и по расписанию.
//
// Кнопка публичная, без авторизации — чтобы не давать задваивать прогоны,
// перед диспатчем проверяем, нет ли уже активного запуска, и просто
// отказываем (а не ставим в очередь), пока текущий не закончится.

const OWNER = "qoparu";
const REPO = "Threads-Scraper";
const WORKFLOW = "hourly-scrape.yml";
const API = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}`;

function ghHeaders() {
  return {
    Authorization: `Bearer ${process.env.GH_ACTIONS_TOKEN}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "jaspulse-dashboard",
  };
}

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ error: "method not allowed" });
    return;
  }
  if (!process.env.GH_ACTIONS_TOKEN) {
    res.status(500).json({ error: "GH_ACTIONS_TOKEN не настроен на Vercel" });
    return;
  }

  try {
    const runsRes = await fetch(`${API}/runs?status=in_progress&per_page=1`, { headers: ghHeaders() });
    const queuedRes = await fetch(`${API}/runs?status=queued&per_page=1`, { headers: ghHeaders() });
    const [runsData, queuedData] = await Promise.all([runsRes.json(), queuedRes.json()]);
    const active = (runsData.workflow_runs || [])[0] || (queuedData.workflow_runs || [])[0];
    if (active) {
      res.status(409).json({ error: "already_running", run_id: active.id });
      return;
    }

    const dispatchRes = await fetch(`${API}/dispatches`, {
      method: "POST",
      headers: { ...ghHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ ref: "main" }),
    });
    if (dispatchRes.status !== 204) {
      const text = await dispatchRes.text();
      res.status(502).json({ error: "dispatch_failed", detail: text });
      return;
    }
    res.status(200).json({ ok: true });
  } catch (e) {
    res.status(502).json({ error: String(e) });
  }
};
