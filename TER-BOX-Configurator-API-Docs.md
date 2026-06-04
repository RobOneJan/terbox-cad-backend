---
tags: [ter-box, architecture, api, configurator, frontend]
created: 2026-04-22
type: technical-reference
---

# TER BOX — Configurator Architecture & API Reference

> [!info] Purpose
> This document is a machine-readable technical reference for the TER BOX frontend application. It describes the configurator module in detail — its data model, state structure, API flows, and component logic — so that an AI assistant or developer can understand the full system before building or connecting a backend API.

---

## 1. Project Overview

**TER BOX** is a modular bicycle storage and urban solution marketplace. The application allows users to configure a custom TER Box product and request a quote.

| Property | Value |
|---|---|
| Framework | React 18.3 + TypeScript 5.8 |
| Build Tool | Vite 5.4 (SWC) |
| Routing | React Router DOM v6 |
| State Management | React Context API + local `useState` |
| UI Components | shadcn-ui (Radix UI primitives) |
| Styling | Tailwind CSS 3.4 |
| Backend | Supabase (PostgreSQL + Edge Functions) |
| Data Fetching | TanStack React Query v5 |
| Forms | React Hook Form v7 + Zod v3 |
| Languages | de, en, nl, fr, es |
| Dev Port | `localhost:8080` |

**Entry Point**: `src/main.tsx`  
**Router**: `src/App.tsx`  
**Configurator Route**: `/configurator` → `src/pages/ConfiguratorPage.tsx` → `src/components/Configurator.tsx`

---

## 2. File Structure (Relevant Paths)

```
/src
├── App.tsx                          ← Route definitions
├── main.tsx                         ← Root render + providers
├── pages/
│   └── ConfiguratorPage.tsx         ← SEO wrapper for configurator
├── components/
│   └── Configurator.tsx             ← Core configurator logic (1,339 lines)
├── contexts/
│   └── LanguageContext.tsx          ← i18n context (5 languages, 300+ keys)
├── hooks/
│   ├── use-mobile.tsx               ← Breakpoint hook (768px)
│   └── use-toast.ts                 ← Toast notification hook
├── integrations/supabase/
│   ├── client.ts                    ← Supabase JS client instance
│   └── types.ts                     ← Auto-generated DB types
└── assets/                          ← Static images, material previews

/supabase/functions/
└── send-email/index.ts              ← Deno edge function for email sending
```

---

## 3. Configurator Module — Full Data Model

The configurator is a **multi-step product customization wizard**. All state lives locally in `Configurator.tsx` using React `useState`. There is no global store for configuration data.

### 3.1 TypeScript Types

```typescript
type UseCaseType = "urban" | "gastronomy" | "combined";
type SizeOption   = "small" | "medium" | "large";
type FloorOption  = "withFloor" | "withoutFloor";
type MountingOption = "noMounting" | "bolted" | "underPaving" | "concrete";
type WallMaterial = "wpc" | "realWood" | "glass" | "meshFence" | "meshFenceWithPrivacy" | "corrugatedSheet";
type WallHeight   = "full" | "half" | "none";
type FloorMaterial = "wpcFloor" | "woodFloor";
type FloorWoodType = "bankirai" | "douglas";
type WpcColor     = "cedar" | "darkGrey" | "teak" | "ipe" | "lightGrey";
type GlassType    = "frosted" | "clear";
type WoodType     = "spruce" | "pine" | "larch" | "douglas" | "oak" | "bankirai";
type ClosureType  = "rollerDoor" | "doubleDoor" | "singleDoor" | "slidingDoor" | "open";
```

### 3.2 Full Configuration State Object

This is the complete shape of a configuration as it exists in component state and as it gets sent to the API:

```typescript
interface TerBoxConfiguration {
  // Use case
  useCase: UseCaseType;             // "urban" | "gastronomy" | "combined"

  // Dimensions
  size: SizeOption;                 // "small" | "medium" | "large"
  customSize?: {
    width: string;                  // in mm or cm (user-entered)
    height: string;
    length: string;
  };

  // Mounting
  mounting: MountingOption;         // "noMounting" | "bolted" | "underPaving" | "concrete"

  // Base frame color
  color: string;                    // RAL color id (e.g. "ral9005") or "other"
  customColor?: string;             // Free-text if color === "other"

  // Floor
  floor: FloorOption;               // "withFloor" | "withoutFloor"
  floorMaterial?: FloorMaterial;    // "wpcFloor" | "woodFloor" — only if floor === "withFloor"
  floorWpcColor?: WpcColor;         // only if floorMaterial === "wpcFloor"
  floorWoodType?: FloorWoodType;    // "bankirai" | "douglas" — only if floorMaterial === "woodFloor"

  // Wall system
  wallHeight: WallHeight;           // "full" | "half" | "none"
  wallMaterial?: WallMaterial;      // only if wallHeight !== "none"
  wpcColor?: WpcColor;              // only if wallMaterial === "wpc"
  glassType?: GlassType;            // only if wallMaterial === "glass"
  woodType?: WoodType;              // only if wallMaterial === "realWood"

  // Closure system (only for useCase !== "gastronomy")
  closureType?: ClosureType;        // "rollerDoor" | "doubleDoor" | "singleDoor" | "slidingDoor" | "open"
  shutterColor?: string;            // RAL color id or "other" — only if closureType === "rollerDoor"
  customShutterColor?: string;      // free-text if shutterColor === "other"
  closureMaterial?: WallMaterial;   // only if closureType is a door (not "rollerDoor" or "open")
  closureWpcColor?: WpcColor;       // only if closureMaterial === "wpc"
  closureGlassType?: GlassType;     // only if closureMaterial === "glass"
  closureWoodType?: WoodType;       // only if closureMaterial === "realWood"

  // Features (multi-select checkboxes)
  features: FeatureKey[];
}

type FeatureKey =
  | "led"           // LED lighting
  | "solar"         // Solar panels
  | "camera"        // Security camera
  | "carCharging"   // Car charging station
  | "bikeCharging"  // E-bike charging
  | "app"           // Smart app control
  | "greening"      // Green roof/wall
  | "power"         // Standard power outlet
  | "highPower"     // High-power outlet
  | "battery"       // Battery storage
  | "heater";       // Heating unit
```

> [!note] Feature Availability
> Not all features are shown for all use cases. Feature visibility is controlled by the `useCase` selection at runtime in the component.

---

## 4. Quote Request Form Data

When the user clicks "Request Quote", a dialog opens with a contact form. The combined payload sent to the backend is:

```typescript
interface QuoteRequestPayload {
  // Contact details
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  company?: string;
  deliveryLocation?: string;
  message?: string;
  referralSource?: string;
  subscribeNewsletter: boolean;

  // Full configuration (see Section 3.2)
  configuration: TerBoxConfiguration;
}
```

---

## 5. Configurator Wizard Steps

The configurator renders as a **multi-step wizard on mobile** and as a **single scrollable page on desktop** (breakpoint: 768px).

Steps are computed dynamically via `useMemo` based on current selections:

| # | Step ID | Condition |
|---|---|---|
| 1 | `useCase` | Always shown |
| 2 | `size` | Always shown |
| 3 | `mounting` | Always shown |
| 4 | `color` | Always shown |
| 5 | `floor` | Always shown |
| 6 | `floorMaterial` | Only if `floor === "withFloor"` |
| 7 | `wallHeight` | Always shown |
| 8 | `wallMaterial` | Only if `wallHeight !== "none"` |
| 9 | `closureType` | Only if `useCase !== "gastronomy"` |
| 10 | `shutterColor` | Only if `closureType === "rollerDoor"` |
| 11 | `closureMaterial` | Only if `closureType` is a door type (not `"rollerDoor"` and not `"open"`) |
| 12 | `features` | Always shown |
| 13 | `summary` | Always shown (final step) |

---

## 6. Available Option Values

### RAL Base Colors (frame)
```
ral9005  ral9016  ral7016  ral7035  ral3000
ral5010  ral6005  ral8017  ral1021  ral2004
```
Plus `"other"` → free-text `customColor` field.

### RAL Shutter Colors (roller door)
```
ral9005  ral9016  ral7016  ral7035  ral3000
ral5010  ral6005  ral8017
```
Plus `"other"` → free-text `customShutterColor` field.

### WPC Colors
`cedar` | `darkGrey` | `teak` | `ipe` | `lightGrey`

### Wood Types (wall)
`spruce` | `pine` | `larch` | `douglas` | `oak` | `bankirai`

### Floor Wood Types
`bankirai` | `douglas`

### Glass Types
`frosted` | `clear`

---

## 7. Current Backend & API Integration

### 7.1 Supabase Client

```typescript
// src/integrations/supabase/client.ts
import { createClient } from "@supabase/supabase-js";

const supabase = createClient<Database>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,
  {
    auth: {
      storage: localStorage,
      persistSession: true,
      autoRefreshToken: true,
    }
  }
);
```

**Environment Variables Required**:
```
VITE_SUPABASE_URL
VITE_SUPABASE_PUBLISHABLE_KEY
VITE_SUPABASE_PROJECT_ID
```

### 7.2 Database Schema — `contact_requests` Table

```typescript
// From src/integrations/supabase/types.ts
interface ContactRequest {
  id: string;                   // UUID, auto-generated PK
  created_at: string;           // ISO timestamp
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  company?: string;
  product?: string;             // Stores "{useCase} - {size}" for quotes
  message?: string;             // Stores features + user message for quotes
  request_type: string;         // "contact" | "quote" | "appointment" | "investor" | "download" | "business-plan"
}
```

> [!warning] Current Limitation
> The `contact_requests` table stores configuration as a formatted string in `product` and `message` fields. There is **no dedicated table** for storing structured configuration data. A proper API would need a new table or JSONB column to store the full `TerBoxConfiguration` object.

### 7.3 Current Quote Submission Flow

```typescript
// Triggered by: handleSubmitQuote() in Configurator.tsx (line ~238)

// Step 1: Write to database
await supabase
  .from("contact_requests")
  .insert({
    first_name: formData.firstName,
    last_name: formData.lastName,
    email: formData.email,
    product: `${configuration.useCase} - ${configuration.size}`,     // flattened
    message: `Features: ${configuration.features.join(", ")}\n\nNachricht: ${formData.message}`,
    request_type: "quote",
  });

// Step 2: Trigger email notification
await supabase.functions.invoke("send-email", {
  body: {
    type: "quote",
    data: {
      ...formData,           // contact fields
      configuration,         // full TerBoxConfiguration object
      subscribeNewsletter,
    },
  },
});

// Step 3: Navigate to thank-you page
navigate("/danke");
```

### 7.4 Edge Function: `send-email`

**Location**: `supabase/functions/send-email/index.ts`  
**Runtime**: Deno  
**Trigger**: HTTP POST via `supabase.functions.invoke("send-email", { body })`

**Supported `type` values**:
```
"contact" | "quote" | "appointment" | "investor" | "download" | "business-plan"
```

**Request body for type `"quote"`**:
```typescript
{
  type: "quote",
  data: {
    firstName: string,
    lastName: string,
    email: string,
    phone?: string,
    company?: string,
    deliveryLocation?: string,
    message?: string,
    referralSource?: string,
    subscribeNewsletter: boolean,
    configuration: TerBoxConfiguration,
  }
}
```

**Security**:
- Rate limiting: 5 requests per IP per minute (in-memory)
- Email validation (RFC regex, max 255 chars)
- Input length limits: firstName/lastName ≤ 100, company ≤ 200, message ≤ 5000
- HTML escaping to prevent XSS

**SMTP Environment Variables** (set in Supabase dashboard):
```
SMTP_HOST
SMTP_PORT      (default: 587)
SMTP_USER
SMTP_PASSWORD
```
Sends to: `info@ter-box.com`

---

## 8. AB1000 CAD Backend API

The TER BOX CAD backend exposes two endpoints for the AB1000 modular box configurator. Both require the header `X-API-Key`.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ab1000/preview` | Returns a GLB (binary glTF 2.0) 3D preview |
| `POST` | `/ab1000/bom` | Returns a bill of materials (JSON) |

### Request Body — `BoxConfig`

```typescript
interface BoxConfig {
  // Dimensions (mm) — clamped: length ≤ 12 000, width ≤ 2 500, height ≤ 3 000
  length_mm: number;
  width_mm:  number;
  height_mm: number;

  // Structure
  with_roof:  boolean;           // default true
  with_floor: boolean;           // default true

  // Walls
  walls: "full" | "half" | "none";                         // default "full"
  wall_material?: "wpc" | "realWood" | "glass" | "meshFence" | "meshFenceWithPrivacy" | "corrugatedSheet";
  wall_wpc_color?: "cedar" | "darkGrey" | "teak" | "ipe" | "lightGrey";

  // Floor
  floor_material?:  "wpcFloor" | "woodFloor";
  floor_wpc_color?: "cedar" | "darkGrey" | "teak" | "ipe" | "lightGrey";

  // Roller door
  roller_door:        boolean;   // default false
  roller_door_color?: string;    // RAL code, e.g. "ral9005"

  // Solar panels (requires with_roof: true)
  with_solar: boolean;           // default false

  // Frame / steel color
  frame_color?: FrameColor | null;   // default null → steel grey
}

type FrameColor =
  | "tiefschwarz"       // RAL 9005 — Tiefschwarz
  | "verkehrsweiss"     // RAL 9016 — Verkehrsweiß
  | "anthrazitgrau"     // RAL 7016 — Anthrazitgrau
  | "lichtgrau"         // RAL 7035 — Lichtgrau
  | "feuerrot"          // RAL 3000 — Feuerrot
  | "enzianblau"        // RAL 5010 — Enzianblau
  | "moosgruen"         // RAL 6005 — Moosgrün
  | "schokoladenbraun"; // RAL 8017 — Schokoladenbraun
```

### Frame color notes

- `frame_color` applies to all steel components: connectors (Y-Ecke, L-Ecke, T-Ecke), all tubes, middle posts, roof substructure, bolts, C-channel rails (Schienen), and roller-door housing.
- When `null` (default), steel grey `#ADADB2` is used.
- When `roller_door_color` is also set, the door housing uses `roller_door_color`; the rest of the frame keeps `frame_color`.

### `/ab1000/preview` Response

Binary GLB (`model/gltf-binary`), `Content-Disposition: attachment; filename=ab1000_preview.glb`.

### `/ab1000/bom` Response

```typescript
interface BOMResponse {
  items: BOMItem[];
  total_parts: number;
}

interface BOMItem {
  component_key: string;
  article_nr:    string;
  description:   string;
  qty:           number;
  length_mm?:    number;
  note?:         string;
}
```

---

## 10. Planned API — Design Guidance

> [!tip] For AI Assistants
> This section describes what a new backend API for the configurator should do, based on the existing frontend structure. Use this when generating API endpoint definitions, OpenAPI specs, or backend implementations.

### 8.1 What the API Needs to Do

The frontend currently calls Supabase directly. A dedicated REST or RPC API would:

1. **Accept a full `QuoteRequestPayload`** (configuration + contact form)
2. **Validate the payload** server-side (Zod schema or equivalent)
3. **Persist the configuration** in a structured format (not as a flat string)
4. **Trigger email notifications** (replacing the current edge function call)
5. **Return a success/error response** for the frontend to handle

### 8.2 Suggested API Endpoint

```
POST /api/quotes
Content-Type: application/json

Body: QuoteRequestPayload (see Section 4)

Success Response (201):
{
  "id": "uuid",
  "status": "received",
  "message": "Quote request received"
}

Error Response (422):
{
  "error": "validation_failed",
  "details": [ ... ]
}
```

### 8.3 Frontend Integration Point

**File**: `src/components/Configurator.tsx`  
**Function**: `handleSubmitQuote()` (around line 238)  
**Current code** calls `supabase.from(...)` and `supabase.functions.invoke(...)`.

To switch to a REST API, replace with:

```typescript
const response = await fetch("/api/quotes", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    ...formData,
    configuration,
    subscribeNewsletter,
  }),
});

if (!response.ok) {
  throw new Error("Submission failed");
}

navigate("/danke");
```

### 8.4 Suggested Database Schema for API

A structured configuration table would look like:

```sql
CREATE TABLE quote_requests (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ DEFAULT NOW(),

  -- Contact
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  email           TEXT NOT NULL,
  phone           TEXT,
  company         TEXT,
  delivery_location TEXT,
  message         TEXT,
  referral_source TEXT,
  subscribe_newsletter BOOLEAN DEFAULT FALSE,

  -- Configuration (structured)
  use_case        TEXT NOT NULL,    -- urban | gastronomy | combined
  size            TEXT NOT NULL,    -- small | medium | large
  custom_width    TEXT,
  custom_height   TEXT,
  custom_length   TEXT,
  mounting        TEXT NOT NULL,
  color           TEXT NOT NULL,
  custom_color    TEXT,
  floor           TEXT NOT NULL,
  floor_material  TEXT,
  floor_wpc_color TEXT,
  floor_wood_type TEXT,
  wall_height     TEXT NOT NULL,
  wall_material   TEXT,
  wpc_color       TEXT,
  glass_type      TEXT,
  wood_type       TEXT,
  closure_type    TEXT,
  shutter_color   TEXT,
  custom_shutter_color TEXT,
  closure_material TEXT,
  closure_wpc_color TEXT,
  closure_glass_type TEXT,
  closure_wood_type TEXT,
  features        TEXT[],           -- array of FeatureKey values

  status          TEXT DEFAULT 'new'  -- new | processing | completed
);
```

---

## 11. i18n — Language System

**Context**: `src/contexts/LanguageContext.tsx`

```typescript
const { t, language, setLanguage } = useLanguage();

// language: "de" | "en" | "nl" | "fr" | "es"
// t("key") returns translated string
```

**Language detection**: Set via URL parameter `?lang=de` or user selection.  
**Storage**: Not persisted (resets on reload unless URL param is present).  
**Configurator keys** (sample): `configurator.title`, `configurator.step1`, `configurator.urban`, `configurator.feature.led`, etc.

An API response does **not** need to be localized — all translations are handled client-side.

---

## 12. Key Observations for API Integration

> [!important] Things to Know Before Building the API

1. **No authentication** — The configurator is fully public. The API endpoint should not require auth tokens. Rate limiting should be the primary protection.

2. **Configuration is context-dependent** — Many fields are conditionally present. The API must handle `undefined`/`null` gracefully for optional fields.

3. **Features are an array** — `features: string[]` can be empty (`[]`) or contain up to 11 values.

4. **Custom colors/sizes are free text** — Validate max length but do not restrict format. Users may enter manufacturer color codes, metric dimensions, etc.

5. **"other" is a sentinel value** — When `color === "other"`, the actual color is in `customColor`. Same for `shutterColor`.

6. **Gastronomy has no closure** — When `useCase === "gastronomy"`, skip `closureType` and all closure-related fields entirely.

7. **Email notification is critical** — The current flow always triggers an email. The API must also send an email (or trigger a webhook) on successful submission.

8. **The `/danke` route** — After successful submission, the frontend navigates to `/danke`. The API only needs to confirm success; it does not control routing.

9. **Form validation is currently client-side only** — There is no Zod validation on the backend. A new API should validate all required fields server-side.

10. **The `send-email` edge function already handles configuration formatting** — If keeping Supabase, this function can remain. Only the DB insert logic needs restructuring.

---

## 13. Component Responsibility Map

| Component | File | Role in configurator |
|---|---|---|
| `ConfiguratorPage` | `src/pages/ConfiguratorPage.tsx` | SEO/Helmet wrapper, renders `<Configurator />` |
| `Configurator` | `src/components/Configurator.tsx` | All state, all steps, form, submission |
| `LanguageContext` | `src/contexts/LanguageContext.tsx` | Provides `t()` translation function |
| `useIsMobile` | `src/hooks/use-mobile.tsx` | Determines wizard vs. scroll layout |
| Supabase client | `src/integrations/supabase/client.ts` | Current data layer |
| `send-email` fn | `supabase/functions/send-email/index.ts` | Email dispatch on form submit |

---

## 14. Routing Reference

```
/                → Index (landing page)
/configurator    → ConfiguratorPage (this module)
/danke           → ThankYouPage (redirect after successful quote)
/kontakt         → ContactPage
/bike-box        → BikeBoxPage
/gastro-box      → GastroBoxPage
/compact-box     → CompactBoxPage
/combi-box       → CombiBoxPage
```

All routes defined in `src/App.tsx`.
