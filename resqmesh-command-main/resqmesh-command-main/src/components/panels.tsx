import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  api,
  correlate,
  SOPS,
  CATEGORIES,
  SEVERITIES,
  LANDMARKS,
  type Incident,
  type Message,
  type Report,
  type ResourceRequest,
  type Severity,
  type IncidentStatus,
} from "@/lib/resqmesh";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle2, GitMerge, Plus, Radio, Send, Split, Truck } from "lucide-react";

export function SeverityBadge({ severity }: { severity: Severity }) {
  const map: Record<Severity, string> = {
    critical: "bg-severity-critical/15 text-severity-critical border-severity-critical/50",
    high: "bg-severity-high/15 text-severity-high border-severity-high/50",
    medium: "bg-severity-medium/15 text-severity-medium border-severity-medium/50",
    low: "bg-severity-low/15 text-severity-low border-severity-low/50",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest ${map[severity] ?? map.low}`}
    >
      {severity === "critical" && (
        <span className="size-1.5 rounded-full bg-severity-critical glow-critical" />
      )}
      {severity}
    </span>
  );
}

export function PanelHeading({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="mb-3 flex items-baseline justify-between">
      <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-primary">{title}</h2>
      {hint ? <span className="font-mono text-[10px] text-muted-foreground">{hint}</span> : null}
    </div>
  );
}

/* ------------------------------- Incident table ------------------------------- */

export function IncidentTable({
  incidents,
  onStatusChange,
  onSelect,
}: {
  incidents: Incident[];
  onStatusChange: (id: string, status: IncidentStatus) => void;
  onSelect: (i: Incident) => void;
}) {
  const [sortKey, setSortKey] = useState<"severity" | "created_at" | "title">("severity");
  const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  const rows = useMemo(
    () =>
      [...incidents].sort((a, b) => {
        if (sortKey === "severity") return (order[a.severity] ?? 9) - (order[b.severity] ?? 9);
        if (sortKey === "title") return a.title.localeCompare(b.title);
        return (b.created_at ?? "").localeCompare(a.created_at ?? "");
      }),
    [incidents, sortKey],
  );

  return (
    <div className="panel-surface flex min-h-0 flex-1 flex-col p-4">
      <PanelHeading title="Active Incidents" hint={`${rows.length} tracked`} />
      <ScrollArea className="min-h-0 flex-1">
        <table className="w-full text-left text-sm">
          <thead className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <tr>
              {(["title", "severity", "created_at"] as const).map((k) => (
                <th key={k} className="pb-2 pr-3">
                  <button className="hover:text-primary" onClick={() => setSortKey(k)}>
                    {k === "created_at" ? "opened" : k}
                  </button>
                </th>
              ))}
              <th className="pb-2 pr-3">category</th>
              <th className="pb-2 pr-3">reports</th>
              <th className="pb-2">status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((inc) => (
              <tr key={inc.incident_id} className="border-t border-border/70">
                <td className="py-2 pr-3">
                  <button
                    className="text-left font-medium hover:text-primary"
                    onClick={() => onSelect(inc)}
                  >
                    {inc.title}
                  </button>
                </td>
                <td className="py-2 pr-3">
                  <SeverityBadge severity={inc.severity} />
                </td>
                <td className="py-2 pr-3 font-mono text-xs text-muted-foreground">
                  {inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : "—"}
                </td>
                <td className="py-2 pr-3 font-mono text-xs uppercase">{inc.category}</td>
                <td className="py-2 pr-3 font-mono text-xs">{inc.reports?.length ?? 0}</td>
                <td className="py-2">
                  <Select
                    value={inc.status}
                    onValueChange={(v) => onStatusChange(inc.incident_id, v as IncidentStatus)}
                  >
                    <SelectTrigger className="h-8 w-36 font-mono text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(["open", "in_progress", "resolved", "closed"] as const).map((s) => (
                        <SelectItem key={s} value={s} className="font-mono text-xs">
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-sm text-muted-foreground">
                  No incidents match the current filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </ScrollArea>
    </div>
  );
}

/* --------------------------- AI duplicate correlation -------------------------- */

export function IncidentReviewCard({
  reports,
  incidents,
  onRefresh,
}: {
  reports: Report[];
  incidents: Incident[];
  onRefresh: () => void;
}) {
  const [resolved, setResolved] = useState<Record<string, string>>({});

  const candidates = useMemo(
    () =>
      reports
        .filter((r) => !r.incident_id)
        .map((r) => ({ report: r, match: correlate(r, incidents) }))
        .filter((c) => c.match !== null)
        .slice(0, 8),
    [reports, incidents],
  );

  const key = (r: Report) => r.report_id ?? r.description;

  const merge = async (r: Report, inc: Incident) => {
    if (!r.report_id) return;
    try {
      await api.attachReport(r.report_id, inc.incident_id);
      setResolved((s) => ({ ...s, [key(r)]: `Merged into ${inc.title}` }));
      toast.success("Report linked to master incident");
      onRefresh();
    } catch (e) {
      toast.error(`Merge failed: ${(e as Error).message}`);
    }
  };

  const spawn = async (r: Report) => {
    try {
      await api.createIncident({
        title: `${r.category.toUpperCase()} — Field Report ${r.device_id}`,
        category: r.category,
        severity: "high",
        latitude: r.latitude,
        longitude: r.longitude,
        summary: r.description,
        status: "open",
      });
      setResolved((s) => ({ ...s, [key(r)]: "Spawned as new incident" }));
      toast.success("New incident spawned from field report");
      onRefresh();
    } catch (e) {
      toast.error(`Spawn failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="panel-surface p-4">
      <PanelHeading title="AI Duplicate Correlation" hint="confidence ≥ 45%" />
      <div className="space-y-3">
        {candidates.map(({ report, match }) => {
          const k = key(report);
          if (resolved[k])
            return (
              <div
                key={k}
                className="rounded-md border border-severity-low/40 bg-severity-low/10 p-3 font-mono text-xs text-severity-low"
              >
                <CheckCircle2 className="mr-1 inline size-3.5" /> {resolved[k]}
              </div>
            );
          return (
            <div key={k} className="rounded-md border border-border bg-card p-3">
              <div className="flex items-center justify-between">
                <span className="rounded bg-primary/15 px-2 py-0.5 font-mono text-[11px] text-primary">
                  {Math.round((match?.score ?? 0) * 100)}% Match
                </span>
                <span className="font-mono text-[10px] uppercase text-muted-foreground">
                  {report.device_id}
                </span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Master: <span className="text-foreground">{match?.incident.title}</span>
              </p>
              <p className="mt-1 line-clamp-3 text-xs italic text-muted-foreground">
                “{report.description}”
              </p>
              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => void merge(report, match!.incident)}
                >
                  <GitMerge className="size-3.5" /> Approve Merge
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => void spawn(report)}
                >
                  <Split className="size-3.5" /> Spawn New
                </Button>
              </div>
            </div>
          );
        })}
        {!candidates.length && (
          <p className="py-6 text-center text-xs text-muted-foreground">
            No probable duplicates awaiting review.
          </p>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------- SOP panel --------------------------------- */

export function SopPanel({ incident }: { incident: Incident | null }) {
  const steps = SOPS[incident?.category ?? ""] ?? SOPS["default"]!;
  return (
    <div className="panel-surface p-4">
      <PanelHeading
        title="Emergency SOP Guidance"
        hint={incident ? incident.category.toUpperCase() : "GENERAL"}
      />
      <ol className="space-y-2">
        {steps.map((s, i) => (
          <li key={i} className="flex gap-3 rounded-md border border-border bg-card p-3 text-xs">
            <span className="font-mono text-accent">0{i + 1}</span>
            <span className="text-muted-foreground">{s}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* ------------------------------ Resource dispatch ------------------------------ */

export function ResourceDispatchPanel({
  resources,
  incident,
  onRefresh,
}: {
  resources: ResourceRequest[];
  incident: Incident | null;
  onRefresh: () => void;
}) {
  const [type, setType] = useState("");
  const [qty, setQty] = useState("1");
  const [busy, setBusy] = useState<string | null>(null);

  const tone: Record<string, string> = {
    pending: "text-severity-medium border-severity-medium/50 bg-severity-medium/10",
    dispatched: "text-primary border-primary/50 bg-primary/10",
    fulfilled: "text-severity-low border-severity-low/50 bg-severity-low/10",
  };

  const request = async (status: "pending" | "dispatched", resource_type: string, quantity: number) => {
    setBusy(resource_type);
    try {
      await api.createResource({
        requester_id: "CMD-DESKTOP-01",
        resource_type,
        quantity,
        urgency: incident?.severity === "critical" ? "critical" : "medium",
        status,
        incident_id: incident?.incident_id ?? null,
      });
      toast.success(
        status === "dispatched" ? `Dispatched ${quantity}x ${resource_type}` : `Requested ${quantity}x ${resource_type}`,
      );
      onRefresh();
    } catch (e) {
      toast.error(`Dispatch failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="panel-surface p-4">
      <PanelHeading title="Resource & Team Dispatch" hint={incident?.title ?? "All units"} />
      <div className="mb-3 flex gap-2">
        <Input
          value={type}
          onChange={(e) => setType(e.target.value)}
          placeholder="Resource type (e.g. Inflatable Boats)"
          className="text-xs"
        />
        <Input
          value={qty}
          onChange={(e) => setQty(e.target.value)}
          className="w-16 text-xs"
          inputMode="numeric"
        />
        <Button
          size="sm"
          variant="outline"
          disabled={!type.trim()}
          onClick={() => void request("pending", type.trim(), Number(qty) || 1).then(() => setType(""))}
        >
          Request
        </Button>
      </div>
      <div className="space-y-2">
        {resources.map((r, i) => {
          const st = r.status ?? "pending";
          return (
            <div
              key={r.resource_id ?? i}
              className="flex items-center justify-between rounded-md border border-border bg-card p-3"
            >
              <div>
                <p className="text-sm">
                  <span className="font-mono text-accent">{r.quantity}x</span> {r.resource_type}
                </p>
                <span
                  className={`mt-1 inline-block rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase ${tone[st] ?? tone["pending"]}`}
                >
                  {st} · {r.urgency ?? "medium"}
                </span>
              </div>
              <Button
                size="sm"
                variant={st === "pending" ? "default" : "outline"}
                disabled={st !== "pending" || busy === r.resource_type}
                onClick={() => void request("dispatched", r.resource_type, r.quantity)}
              >
                <Truck className="size-3.5" /> {st === "pending" ? "Dispatch Team" : "En route"}
              </Button>
            </div>
          );
        })}
        {!resources.length && (
          <p className="py-6 text-center text-xs text-muted-foreground">
            No resource requests logged.
          </p>
        )}
      </div>
    </div>
  );
}

/* --------------------------------- Mesh chat ---------------------------------- */

export function MeshChat({
  messages,
  incident,
  onSent,
}: {
  messages: Message[];
  incident: Incident | null;
  onSent: () => void;
}) {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);

  const send = async () => {
    if (!text.trim()) return;
    setSending(true);
    try {
      await api.sendMessage({
        sender_device_id: "CMD-DESKTOP-01",
        sender_user_id: "commander-1",
        text: text.trim(),
        incident_id: incident?.incident_id ?? null,
      });
      setText("");
      onSent();
    } catch (e) {
      toast.error(`Broadcast failed: ${(e as Error).message}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="panel-surface flex h-96 flex-col p-4">
      <PanelHeading title="Mesh Tactical Chat" hint="P2P broadcast" />
      <ScrollArea className="min-h-0 flex-1 pr-2">
        <div className="space-y-2">
          {messages.map((m, i) => {
            const mine = m.sender_device_id === "CMD-DESKTOP-01";
            return (
              <div
                key={m.message_id ?? i}
                className={`rounded-md border p-2 text-xs ${
                  mine ? "border-primary/40 bg-primary/10" : "border-border bg-card"
                }`}
              >
                <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  <Radio className="mr-1 inline size-3" />
                  {m.sender_user_id} · {m.sender_device_id}
                </p>
                <p className="mt-1">{m.text}</p>
              </div>
            );
          })}
          {!messages.length && (
            <p className="py-6 text-center text-xs text-muted-foreground">Mesh channel is quiet.</p>
          )}
        </div>
      </ScrollArea>
      <div className="mt-3 flex gap-2">
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void send()}
          placeholder="Broadcast to mesh…"
          className="font-mono text-xs"
        />
        <Button onClick={() => void send()} disabled={sending}>
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  );
}

/* ------------------------------ New incident modal ----------------------------- */

export function NewIncidentDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [selectedLandmarkId, setSelectedLandmarkId] = useState("central-majestic");
  const [landmarkDetail, setLandmarkDetail] = useState("");
  const [showAdvancedGps, setShowAdvancedGps] = useState(false);
  const [form, setForm] = useState({
    title: "",
    category: "fire",
    severity: "high" as Severity,
    latitude: "12.9767",
    longitude: "77.5713",
    summary: "",
  });

  const handleLandmarkChange = (landmarkId: string) => {
    setSelectedLandmarkId(landmarkId);
    const landmark = LANDMARKS.find((l) => l.id === landmarkId);
    if (landmark && landmarkId !== "custom") {
      setForm((prev) => ({
        ...prev,
        latitude: String(landmark.lat),
        longitude: String(landmark.lng),
      }));
    }
  };

  const submit = async () => {
    try {
      const selectedLandmark = LANDMARKS.find((l) => l.id === selectedLandmarkId);
      const landmarkLocation =
        selectedLandmarkId === "custom"
          ? landmarkDetail || "Field Location"
          : `${selectedLandmark?.name ?? ""}${landmarkDetail ? ` (${landmarkDetail})` : ""}`;

      const finalTitle = form.title.trim();
      const finalSummary = form.summary.trim()
        ? `[Location: ${landmarkLocation}] ${form.summary.trim()}`
        : `Reported at ${landmarkLocation}`;

      await api.createIncident({
        title: finalTitle,
        category: form.category,
        severity: form.severity,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        summary: finalSummary,
        status: "open",
      });
      toast.success("Incident registered successfully");
      setOpen(false);
      setForm({ ...form, title: "", summary: "" });
      setLandmarkDetail("");
      onCreated();
    } catch (e) {
      toast.error(`Create failed: ${(e as Error).message}`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> New Incident
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-mono uppercase tracking-widest text-base">
            🚨 Register Incident
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-3.5 pt-1">
          <div>
            <Label className="text-xs font-semibold text-foreground">Incident Title *</Label>
            <Input
              placeholder="e.g. Chemical Storage Warehouse Fire"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="mt-1"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs font-semibold text-foreground">Category</Label>
              <Select
                value={form.category}
                onValueChange={(v) => setForm({ ...form, category: v })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c} className="capitalize">
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs font-semibold text-foreground">Severity Level</Label>
              <Select
                value={form.severity}
                onValueChange={(v) => setForm({ ...form, severity: v as Severity })}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITIES.map((s) => (
                    <SelectItem key={s} value={s} className="capitalize">
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Locality & Landmark Picker */}
          <div className="rounded-lg border border-border/80 bg-card/60 p-3 space-y-2.5">
            <div>
              <Label className="text-xs font-semibold text-primary">
                📍 Locality / Landmark Sector *
              </Label>
              <Select value={selectedLandmarkId} onValueChange={handleLandmarkChange}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANDMARKS.map((lm) => (
                    <SelectItem key={lm.id} value={lm.id}>
                      {lm.name} ({lm.area})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-xs text-muted-foreground">
                Specific Landmark / Street Details (Optional)
              </Label>
              <Input
                placeholder="e.g. Near Gate 2 opposite fuel station / Metro Pillar 180"
                value={landmarkDetail}
                onChange={(e) => setLandmarkDetail(e.target.value)}
                className="mt-1 text-xs"
              />
            </div>

            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowAdvancedGps(!showAdvancedGps)}
                className="text-[11px] font-mono text-muted-foreground hover:text-primary underline cursor-pointer"
              >
                {showAdvancedGps ? "− Hide GPS Coordinates" : "+ Advanced: Custom GPS Coordinates"}
              </button>
            </div>

            {showAdvancedGps && (
              <div className="grid grid-cols-2 gap-2 pt-1">
                <div>
                  <Label className="text-[10px] text-muted-foreground">Latitude</Label>
                  <Input
                    value={form.latitude}
                    onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                    className="h-7 text-xs font-mono"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-muted-foreground">Longitude</Label>
                  <Input
                    value={form.longitude}
                    onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                    className="h-7 text-xs font-mono"
                  />
                </div>
              </div>
            )}
          </div>

          <div>
            <Label className="text-xs font-semibold text-foreground">Incident Summary / Situation Notes</Label>
            <Textarea
              placeholder="Describe casualty count, immediate hazards, structure damage, or trapped civilians..."
              value={form.summary}
              onChange={(e) => setForm({ ...form, summary: e.target.value })}
              rows={3}
              className="mt-1 text-xs"
            />
          </div>
        </div>
        <DialogFooter className="pt-2">
          <Button onClick={() => void submit()} disabled={!form.title.trim()}>
            Deploy Incident to Mesh
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

