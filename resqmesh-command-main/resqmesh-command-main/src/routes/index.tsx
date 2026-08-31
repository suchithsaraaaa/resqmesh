import { createFileRoute, ClientOnly } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense, useEffect, useState } from "react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ShieldAlert } from "lucide-react";
import {
  api,
  CATEGORIES,
  type Incident,
  type IncidentStatus,
  type Message,
  type Report,
  type ResourceRequest,
} from "@/lib/resqmesh";
import {
  IncidentReviewCard,
  IncidentTable,
  MeshChat,
  NewIncidentDialog,
  ResourceDispatchPanel,
  SopPanel,
} from "@/components/panels";

const IncidentMap = lazy(() => import("@/components/IncidentMap"));

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "ResQMesh AI Command Center — Offline Disaster Response" },
      {
        name: "description",
        content:
          "Offline-first emergency operations dashboard: live incident map, AI duplicate correlation, SOP guidance, resource dispatch and mesh tactical chat.",
      },
      { property: "og:title", content: "ResQMesh AI Command Center" },
      {
        property: "og:description",
        content:
          "Tactical offline-first command center for disaster response: incidents, AI correlation, SOPs, dispatch and mesh chat.",
      },
    ],
  }),
  component: CommandCenter,
});

const FILTERS = ["all", "critical", ...CATEGORIES] as const;

function useClock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return now;
}

function CommandCenter() {
  const qc = useQueryClient();
  const now = useClock();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [selected, setSelected] = useState<Incident | null>(null);

  const opts = { refetchInterval: 10000, retry: 0 } as const;
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, ...opts });
  const incidentsQ = useQuery({
    queryKey: ["incidents"],
    queryFn: () => api.listIncidents(),
    ...opts,
  });
  const reportsQ = useQuery({ queryKey: ["reports"], queryFn: () => api.listReports(), ...opts });
  const messagesQ = useQuery({ queryKey: ["messages"], queryFn: () => api.listMessages(), ...opts });
  const resourcesQ = useQuery({
    queryKey: ["resources"],
    queryFn: () => api.listResources(),
    ...opts,
  });

  const incidents: Incident[] = incidentsQ.data ?? [];
  const reports: Report[] = reportsQ.data ?? [];
  const messages: Message[] = [...(messagesQ.data ?? [])].sort((a, b) =>
    (a.timestamp ?? "").localeCompare(b.timestamp ?? ""),
  );
  const resources: ResourceRequest[] = resourcesQ.data ?? [];
  const online = health.isSuccess;

  const visible = incidents.filter((i) =>
    filter === "all" ? true : filter === "critical" ? i.severity === "critical" : i.category === filter,
  );
  const focus = selected ?? visible[0] ?? null;

  const refresh = (key: string) => void qc.invalidateQueries({ queryKey: [key] });

  const changeStatus = async (id: string, status: IncidentStatus) => {
    try {
      await api.updateIncident(id, { status_val: status });
      toast.success(`Incident set to ${status}`);
      refresh("incidents");
    } catch (e) {
      toast.error(`Update failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Toaster position="top-right" />
      <header className="sticky top-0 z-500 border-b border-border bg-sidebar/95 backdrop-blur">
        <div className="flex flex-wrap items-center gap-4 px-5 py-3">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-md bg-primary/15 text-primary">
              <ShieldAlert className="size-5" />
            </span>
            <div>
              <h1 className="font-mono text-sm font-semibold uppercase tracking-[0.2em] text-foreground">
                ResQMesh AI Command Center
              </h1>
              <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                {health.data?.mode ?? "offline-mesh-operational"} · v{health.data?.version ?? "1.0.0"}
              </p>
            </div>
          </div>

          <span
            className={`rounded border px-2 py-1 font-mono text-[10px] uppercase tracking-widest ${
              online
                ? "border-severity-low/50 bg-severity-low/10 text-severity-low"
                : "border-severity-critical/50 bg-severity-critical/10 text-severity-critical"
            }`}
          >
            ● Mesh Status: {online ? "ACTIVE (Offline P2P Network)" : "LINK DOWN — localhost:8000"}
          </span>

          <div className="ml-auto flex items-center gap-4">
            <div className="text-right font-mono text-[11px] leading-tight text-muted-foreground">
              <div>{now ? `${now.toISOString().slice(11, 19)} UTC` : "--:--:-- UTC"}</div>
              <div className="text-foreground">
                {now ? now.toLocaleTimeString() : "--:--:--"} LOCAL
              </div>
            </div>
            <NewIncidentDialog onCreated={() => refresh("incidents")} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2 px-5 pb-3">
          {FILTERS.map((f) => (
            <Button
              key={f}
              size="sm"
              variant={filter === f ? "default" : "outline"}
              className="h-7 font-mono text-[10px] uppercase tracking-widest"
              onClick={() => setFilter(f)}
            >
              {f === "all" ? "All" : f === "critical" ? "Critical Only" : f}
            </Button>
          ))}
        </div>
      </header>

      <main className="grid flex-1 gap-4 p-5 lg:grid-cols-[3fr_2fr]">
        <section className="flex min-h-0 flex-col gap-4">
          <div className="panel-surface h-[420px] overflow-hidden isolate relative z-0">
            <Suspense
              fallback={
                <div className="grid h-full place-items-center font-mono text-xs text-muted-foreground">
                  Loading tactical map…
                </div>
              }
            >
              <ClientOnly fallback={null}>
                <IncidentMap incidents={visible} onSelect={setSelected} />
              </ClientOnly>
            </Suspense>
          </div>
          <IncidentTable
            incidents={visible}
            onStatusChange={(id, s) => void changeStatus(id, s)}
            onSelect={setSelected}
          />
        </section>

        <section className="min-w-0">
          <Tabs defaultValue="ai">
            <TabsList className="w-full font-mono text-[10px] uppercase tracking-widest">
              <TabsTrigger value="ai">AI Review</TabsTrigger>
              <TabsTrigger value="sop">SOP</TabsTrigger>
              <TabsTrigger value="dispatch">Dispatch</TabsTrigger>
              <TabsTrigger value="chat">Mesh Chat</TabsTrigger>
            </TabsList>
            <TabsContent value="ai" className="mt-4">
              <IncidentReviewCard
                reports={reports}
                incidents={incidents}
                onRefresh={() => {
                  refresh("incidents");
                  refresh("reports");
                }}
              />
            </TabsContent>
            <TabsContent value="sop" className="mt-4">
              <SopPanel incident={focus} />
            </TabsContent>
            <TabsContent value="dispatch" className="mt-4">
              <ResourceDispatchPanel
                incident={focus}
                resources={resources}
                onRefresh={() => refresh("resources")}
              />
            </TabsContent>
            <TabsContent value="chat" className="mt-4">
              <MeshChat
                messages={messages}
                incident={focus}
                onSent={() => refresh("messages")}
              />
            </TabsContent>
          </Tabs>
        </section>
      </main>
    </div>
  );
}
