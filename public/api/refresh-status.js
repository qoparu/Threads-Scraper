// Статус последнего прогона GitHub Actions — для попапа прогресса после
// нажатия «Обновить сейчас». Отдаёт крупные стадии пайплайна, не построчный
// лог (детальный лог парсинга наружу не транслируется).

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

// Крупные стадии, которые видит пользователь — сырые имена шагов GitHub Actions
// сворачиваются в эти три (детальный список шагов внутри hourly-scrape.yml шире).
const STAGES = [
  { key: "setup", label: "Подготовка окружения", steps: [
    "Set up job", "Run actions/checkout@v4", "Run actions/setup-python@v5",
    "Run actions/setup-node@v4", "Restore persistent state (corpus + AI caches)",
    "Install Python deps", "Install Chromium", "Write secrets",
  ]},
  { key: "scrape", label: "Сбор постов + AI-обработка + сборка дашборда", steps: [
    "Run hourly scrape + build + deploy",
  ]},
  { key: "finish", label: "Сохранение данных и завершение", steps: [
    "Save persistent state", "Post Run actions/setup-node@v4",
    "Post Run actions/setup-python@v5", "Post Run actions/checkout@v4", "Complete job",
  ]},
];

function stageStatus(stepNames, jobSteps) {
  const matched = jobSteps.filter((s) => stepNames.includes(s.name));
  if (!matched.length) return "pending";
  if (matched.some((s) => s.status === "in_progress")) return "active";
  if (matched.every((s) => s.status === "completed" && s.conclusion === "success")) return "done";
  if (matched.some((s) => s.conclusion && s.conclusion !== "success")) return "failed";
  return "pending";
}

module.exports = async (req, res) => {
  if (!process.env.GH_ACTIONS_TOKEN) {
    res.status(500).json({ error: "GH_ACTIONS_TOKEN не настроен на Vercel" });
    return;
  }
  try {
    const runsRes = await fetch(`${API}/runs?per_page=1`, { headers: ghHeaders() });
    const runsData = await runsRes.json();
    const run = (runsData.workflow_runs || [])[0];
    if (!run) {
      res.status(200).json({ status: "none" });
      return;
    }

    let jobSteps = [];
    if (run.status !== "queued") {
      const jobsRes = await fetch(`${run.jobs_url}`, { headers: ghHeaders() });
      const jobsData = await jobsRes.json();
      jobSteps = ((jobsData.jobs || [])[0] || {}).steps || [];
    }

    const stages = STAGES.map((s) => ({
      key: s.key,
      label: s.label,
      status: run.status === "queued" ? "pending" : stageStatus(s.steps, jobSteps),
    }));

    res.status(200).json({
      status: run.status,           // queued | in_progress | completed
      conclusion: run.conclusion,   // null | success | failure | cancelled ...
      run_id: run.id,
      html_url: run.html_url,
      created_at: run.created_at,
      stages,
    });
  } catch (e) {
    res.status(502).json({ error: String(e) });
  }
};
