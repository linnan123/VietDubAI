"use client";
import {useCallback, useEffect, useState} from "react";

type Project = {id: string; name: string; description: string};
type Episode = {id: string; name: string; source_sha256: string | null; metadata_json: string | null; approved: boolean};
type Job = {id: string; episode_id: string; status: string; attempts: number; error: string | null};
async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {method, headers: body instanceof FormData ? undefined : {"Content-Type": "application/json"}, body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body)});
  if (!response.ok) { const error = await response.json().catch(() => ({})); throw new Error(typeof error.detail === "string" ? error.detail : `请求失败 (${response.status})`); }
  return response.status === 204 ? undefined as T : response.json();
}
export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState("");
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [episodeName, setEpisodeName] = useState("");
  const refresh = useCallback(async () => {
    const [nextProjects, nextJobs] = await Promise.all([request<Project[]>("/projects"), request<Job[]>("/jobs")]);
    const nextEpisodes = selected && nextProjects.some(project => project.id === selected) ? await request<Episode[]>(`/projects/${selected}/episodes`) : [];
    setProjects(nextProjects); setJobs(nextJobs); setEpisodes(nextEpisodes);
  }, [selected]);
  useEffect(() => {let active = true; const load = () => {if (active) refresh().catch(reason => setError(String(reason)));}; load(); const timer = setInterval(load, 4000); return () => {active = false; clearInterval(timer);};}, [refresh]);
  async function act(action: () => Promise<unknown>) {setBusy(true); setError(""); try {await action(); await refresh();} catch (reason) {setError(String(reason));} finally {setBusy(false);}}
  return <main className="max-w-6xl mx-auto p-6 md:p-12">
    <header className="mb-10"><p className="text-indigo-700 font-semibold">VIETDUB AI / V0.1</p><h1 className="text-3xl font-bold mt-2">中越短剧 · 制作工作台</h1><p className="text-slate-500 mt-3">Phase 1：管理授权内容、上传原片、分析媒体与提取音频。</p></header>
    {error && <p role="alert" className="bg-red-50 text-red-800 p-4 mb-4 rounded">{error}</p>}
    <div className="grid md:grid-cols-[280px_1fr] gap-6">
      <aside className="bg-white p-5 rounded-xl border"><h2 className="font-bold mb-4">项目</h2>
        <form onSubmit={event => {event.preventDefault(); void act(async () => {const item = await request<Project>("/projects", "POST", {name: projectName}); setProjectName(""); setSelected(item.id);});}} className="space-y-2 mb-5"><input aria-label="新项目名称" placeholder="新项目名称" required maxLength={200} value={projectName} onChange={event => setProjectName(event.target.value)}/><button disabled={busy}>创建项目</button></form>
        {!projects.length && <p className="text-slate-500">创建第一个项目以开始制作。</p>}
        {projects.map(project => <button key={project.id} onClick={() => {setSelected(project.id); setEpisodes([]);}} className={`block w-full text-left mb-2 ${selected === project.id ? "bg-indigo-50 border-indigo-400" : ""}`}>{project.name}</button>)}
      </aside>
      <section className="bg-white p-6 rounded-xl border"><h2 className="text-xl font-bold mb-4">剧集与媒体</h2>
        {!selected ? <p className="text-slate-500">请先选择项目。</p> : <>
          <div className="flex gap-2 mb-6"><button disabled={busy} onClick={() => {const name = window.prompt("项目新名称", projects.find(project => project.id === selected)?.name); if (name) void act(() => request(`/projects/${selected}`, "PATCH", {name, description: projects.find(project => project.id === selected)?.description || ""}));}}>重命名项目</button><button disabled={busy} onClick={() => {if (window.confirm("删除空项目？")) void act(async () => {await request(`/projects/${selected}`, "DELETE"); setSelected("");});}}>删除项目</button></div>
          <form className="flex gap-2 mb-6" onSubmit={event => {event.preventDefault(); void act(async () => {await request(`/projects/${selected}/episodes`, "POST", {name: episodeName}); setEpisodeName("");});}}><input aria-label="剧集名称" placeholder="第 01 集" required maxLength={200} value={episodeName} onChange={event => setEpisodeName(event.target.value)}/><button className="shrink-0" disabled={busy}>添加剧集</button></form>
          {!episodes.length && <p className="text-slate-500">暂无剧集。添加剧集后上传带音轨的 MP4。</p>}
          {episodes.map(episode => {const job = jobs.find(item => item.episode_id === episode.id); const metadata = episode.metadata_json ? JSON.parse(episode.metadata_json) as {duration_ms: number; width: number; height: number} : null; return <article key={episode.id} className="border rounded-lg p-4 mb-4 space-y-3">
            <h3 className="font-bold">{episode.name}</h3><p className="text-sm text-slate-600">{episode.approved ? "✓ 人工确认完成" : "等待人工确认"} · {job ? ({queued: "排队中", running: "处理中", succeeded: "分析完成", failed: "处理失败"}[job.status] || job.status) : "待上传"}</p>
            {metadata && <p>{metadata.width} × {metadata.height} · {(metadata.duration_ms / 1000).toFixed(2)} 秒 · WAV 16 kHz / 单声道</p>}
            {job?.error && <p role="alert" className="text-red-700">{job.error}</p>}
            {!episode.source_sha256 && <label className="block text-sm">上传 MP4（最大 512 MiB，需有音轨）<input disabled={busy} type="file" accept=".mp4,video/mp4" onChange={event => {const file = event.target.files?.[0]; if (!file) return; if (file.size > 512 * 1024 * 1024) {setError("文件不能超过 512 MiB"); return;} const form = new FormData(); form.append("file", file); void act(() => request(`/episodes/${episode.id}/upload`, "POST", form));}}/></label>}
            <div className="flex flex-wrap gap-2"><button disabled={busy} onClick={() => {const name = window.prompt("剧集新名称", episode.name); if (name) void act(() => request(`/episodes/${episode.id}`, "PATCH", {name}));}}>重命名</button><button disabled={busy || job?.status === "queued" || job?.status === "running"} onClick={() => {if (window.confirm("删除剧集记录？原片仍保留。")) void act(() => request(`/episodes/${episode.id}`, "DELETE"));}}>删除</button>{job?.status === "failed" && <button disabled={busy} onClick={() => void act(() => request(`/jobs/${job.id}/retry`, "POST"))}>重试处理</button>}{job?.status === "succeeded" && !episode.approved && <button disabled={busy} onClick={() => void act(() => request(`/episodes/${episode.id}/approve`, "POST"))}>确认媒体分析</button>}</div>
          </article>;})}
        </>}
      </section>
    </div><footer className="mt-6 text-sm text-slate-500">原片不可覆盖。仅限已授权内容。识别、翻译与语音合成将在后续阶段开放。</footer>
  </main>;
}
