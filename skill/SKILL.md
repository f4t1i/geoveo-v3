---
name: geoveo-orchestrator
description: Orchestriert geo-konditionierte Video-Generierung aus Route, Street-Level-Bildern, Depth/Conditioning und austauschbaren Video-Backends.
version: 2.0.0
author: OpenAI
tags:
  - geospatial
  - video-generation
  - street-view
  - mapillary
  - routing
  - conditioning
  - orchestration
inputs:
  - name: prompt
    type: string
    required: true
    description: Natürliche Beschreibung der gewünschten Szene oder Fahrt.
  - name: location
    type: string
    required: true
    description: Ort, Gebiet oder Start/Ziel-Region für die Route.
  - name: mode
    type: string
    required: false
    default: drive
    description: Fortbewegungsmodus, z. B. drive, walk, bike.
  - name: sampling_meters
    type: number
    required: false
    default: 15
    description: Abstand zwischen gesampelten Viewpoints entlang der Route.
  - name: imagery_source
    type: string
    required: false
    default: mapillary
    description: Street-Level-Datenquelle, z. B. mapillary oder google_street_view.
  - name: video_backend
    type: string
    required: false
    default: cogvideox_i2v
    description: Ziel-Backend für die Video-Generierung.
---

# GeoVeo Orchestrator Skill

## Purpose
Dieser Skill plant und orchestriert eine **geo-konditionierte Video-Pipeline**:

1. Route aus Nutzerintention ableiten
2. Route in Viewpoints samplen
3. Street-Level-Bilder je Viewpoint abrufen
4. Conditioning-Bundle erzeugen
5. Video-Backend ausführen
6. Ergebnis und Artefakte strukturiert zurückgeben

Der Skill ist für **deterministische, reproduzierbare Render-Jobs** gedacht und soll **modellagnostisch** bleiben.

## When to use
Verwende diesen Skill, wenn der Nutzer:
- eine Fahrt, Bewegung oder Kameraführung an einem realen Ort beschreiben will
- Street-Level-Referenzen in Video-Generierung einbinden will
- eine Route in konsistente Keyframes und Rendering-Schritte überführen will
- zwischen mehreren Video-Backends abstrahieren möchte

## High-level workflow

### Step 1: Interpret request
Extrahiere:
- visuelles Ziel
- Ort/Region
- Bewegungsmodus
- gewünschte Stilhinweise
- gewünschte Datenquelle
- gewünschtes Rendering-Backend

### Step 2: Get route
Erzeuge eine Route oder lineare Kamerabahn über `get_route`.

### Step 3: Sample viewpoints
Sample entlang der Route Viewpoints mit:
- `lat`
- `lng`
- `heading`
- `pitch`
- `fov`

### Step 4: Fetch imagery
Hole Street-Level-Bilder für jeden Viewpoint über `get_street_level_image`.

### Step 5: Build conditioning
Erzeuge ein Conditioning-Bundle mit:
- RGB-Frames
- Depth-Pfaden oder Depth-Hinweisen
- Kamera-Pfad
- Prompt
- Route-Metadaten

### Step 6: Generate video
Übergebe das Conditioning-Bundle an `generate_video`.

### Step 7: Return artifacts
Gib zurück:
- Route
- Keyframes
- Conditioning-Metadaten
- Video-Output
- Status
- Fehler oder Qualitätswarnungen

## Operational rules
- Arbeite deterministisch und reproduzierbar.
- Bevorzuge Caching für identische Viewpoints.
- Nutze segmentweise Verarbeitung bei längeren Routen.
- Vermische keine Quellen ungekennzeichnet.
- Markiere Fallbacks explizit.
- Gib immer strukturierte Outputs zurück.
- Erfinde keine echten Provider-Antworten.

## Tool contracts

### Tool: get_route
Erzeugt eine Route oder Viewpoint-Sequenz aus Ort, Modus und optionalen Constraints.

#### Input schema
```json
{
  "type": "object",
  "properties": {
    "location": {
      "type": "string",
      "description": "Ort, Region oder textuelle Routenbeschreibung."
    },
    "mode": {
      "type": "string",
      "enum": ["drive", "walk", "bike"],
      "default": "drive"
    },
    "sampling_meters": {
      "type": "number",
      "minimum": 1,
      "default": 15
    },
    "max_points": {
      "type": "integer",
      "minimum": 1,
      "default": 20
    }
  },
  "required": ["location"]
}
```

#### Output schema
```json
{
  "type": "object",
  "properties": {
    "route_id": { "type": "string" },
    "mode": { "type": "string" },
    "polyline": { "type": "string" },
    "distance_m": { "type": "number" },
    "points": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "index": { "type": "integer" },
          "lat": { "type": "number" },
          "lng": { "type": "number" },
          "heading_deg": { "type": "number" }
        },
        "required": ["index", "lat", "lng"]
      }
    }
  },
  "required": ["route_id", "points"]
}
```

### Tool: get_street_level_image
Lädt ein Street-Level-Bild für einen gegebenen Viewpoint.

#### Input schema
```json
{
  "type": "object",
  "properties": {
    "lat": { "type": "number" },
    "lng": { "type": "number" },
    "heading_deg": { "type": "number", "default": 0 },
    "pitch_deg": { "type": "number", "default": 0 },
    "fov": { "type": "number", "default": 90 },
    "source": {
      "type": "string",
      "enum": ["mapillary", "google_street_view"],
      "default": "mapillary"
    },
    "size": {
      "type": "string",
      "default": "1024x576"
    },
    "cache_key": {
      "type": "string"
    }
  },
  "required": ["lat", "lng"]
}
```

#### Output schema
```json
{
  "type": "object",
  "properties": {
    "image_id": { "type": "string" },
    "source": { "type": "string" },
    "image_path": { "type": "string" },
    "lat": { "type": "number" },
    "lng": { "type": "number" },
    "heading_deg": { "type": "number" },
    "pitch_deg": { "type": "number" },
    "fov": { "type": "number" },
    "status": {
      "type": "string",
      "enum": ["ok", "fallback", "not_found", "error"]
    }
  },
  "required": ["image_id", "source", "status"]
}
```

### Tool: generate_video
Erzeugt ein Video aus einem Conditioning-Bundle und einem Ziel-Backend.

#### Input schema
```json
{
  "type": "object",
  "properties": {
    "backend": {
      "type": "string",
      "enum": ["cogvideox_i2v", "animatediff_depth", "veo"],
      "default": "cogvideox_i2v"
    },
    "prompt": {
      "type": "string"
    },
    "conditioning_bundle": {
      "type": "object",
      "properties": {
        "route_id": { "type": "string" },
        "frames": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "index": { "type": "integer" },
              "lat": { "type": "number" },
              "lng": { "type": "number" },
              "heading_deg": { "type": "number" },
              "image_path": { "type": "string" },
              "depth_path": { "type": "string" }
            },
            "required": ["index", "image_path"]
          }
        },
        "camera_path": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "frame_index": { "type": "integer" },
              "lat": { "type": "number" },
              "lng": { "type": "number" },
              "heading_deg": { "type": "number" }
            },
            "required": ["frame_index"]
          }
        }
      },
      "required": ["frames"]
    },
    "output_fps": {
      "type": "integer",
      "default": 24
    },
    "duration_seconds": {
      "type": "number",
      "default": 5
    }
  },
  "required": ["backend", "prompt", "conditioning_bundle"]
}
```

#### Output schema
```json
{
  "type": "object",
  "properties": {
    "job_id": { "type": "string" },
    "backend": { "type": "string" },
    "video_path": { "type": "string" },
    "preview_gif_path": { "type": "string" },
    "frames_used": { "type": "integer" },
    "status": {
      "type": "string",
      "enum": ["queued", "running", "done", "failed"]
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["job_id", "backend", "status"]
}
```

## Recommended response format
Antworte nach erfolgreicher Orchestrierung strukturiert mit:

```json
{
  "job_id": "job_001",
  "route_id": "alster_demo_001",
  "status": "done",
  "imagery_source": "mapillary",
  "video_backend": "cogvideox_i2v",
  "artifacts": {
    "route": "artifacts/routes/alster_demo_001.json",
    "conditioning_bundle": "artifacts/conditioning/alster_demo_001.json",
    "video": "artifacts/video/job_001.mp4"
  },
  "warnings": []
}
```

## Failure handling
Wenn ein Teil fehlschlägt:
- gib den letzten erfolgreichen Zustand zurück
- dokumentiere den Fehler explizit
- liefere Teil-Artefakte, wenn vorhanden
- markiere `status` sauber als `failed` oder `partial`

Beispiel:
```json
{
  "job_id": "job_002",
  "status": "failed",
  "failed_step": "get_street_level_image",
  "reason": "No imagery found for sampled route segment",
  "partial_artifacts": {
    "route": "artifacts/routes/job_002_route.json"
  }
}
```

## Notes
- Dieses Skill-Design ist absichtlich backend-agnostisch.
- Street-Level-Quellen, Depth-Systeme und Video-Modelle sollen austauschbar bleiben.
- Für Produktionssysteme sollten Auth, Rate-Limits, Retry-Logik und Cache-Layer ergänzt werden.
