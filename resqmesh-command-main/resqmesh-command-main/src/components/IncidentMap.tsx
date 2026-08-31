import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Incident } from "@/lib/resqmesh";
import { severityColor } from "@/lib/resqmesh";
import { Button } from "@/components/ui/button";

function glowIcon(color: string, pulse: boolean) {
  return L.divIcon({
    className: "",
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    html: `<span style="display:block;width:18px;height:18px;border-radius:9999px;background:${color};box-shadow:0 0 0 4px ${color}33,0 0 18px ${color};${
      pulse ? "animation:resq-pulse 1.4s ease-in-out infinite;" : ""
    }"></span>`,
  });
}

export default function IncidentMap({
  incidents,
  onSelect,
}: {
  incidents: Incident[];
  onSelect: (i: Incident) => void;
}) {
  return (
    <MapContainer
      center={[12.9716, 77.5946]}
      zoom={13}
      className="h-full w-full"
      style={{ background: "#020617" }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution="&copy; OpenStreetMap &copy; CARTO"
      />
      {incidents.map((inc) => (
        <Marker
          key={inc.incident_id}
          position={[inc.latitude, inc.longitude]}
          icon={glowIcon(severityColor[inc.severity] ?? "#38bdf8", inc.severity === "critical")}
        >
          <Popup>
            <div className="min-w-52 space-y-1 font-sans">
              <p className="text-sm font-semibold">{inc.title}</p>
              <p className="text-xs uppercase tracking-wide">
                {inc.category} · {inc.severity}
              </p>
              <p className="text-xs">Linked reports: {inc.reports?.length ?? 0}</p>
              <Button size="sm" className="mt-1 w-full" onClick={() => onSelect(inc)}>
                View Incident Details
              </Button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
