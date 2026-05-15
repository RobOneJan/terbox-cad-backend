# System Architecture

## 1. Goal
The system generates a CAD model based on a user-defined configuration from a web frontend.

---

## 2. Core Principle
Configuration → Rules → Geometry → CAD

The configuration is the single source of truth.

---

## 3. High-Level Architecture

### Backend
- Language: Python  
- Framework: FastAPI  
- Data Models: Pydantic  
- Hosting: GCP Cloud Run  
- CI/CD: GCP Cloud Build  
- Version Control: GitHub  

### CAD Integration
- System: Fusion 360  
- Method: API or script-based manipulation  

### Frontend
- Generated via Lovable  
- Hosted externally  
- Communicates via HTTP API  

---

## 4. System Components

### 4.1 Frontend (Lovable)
- Collects user configuration  
- Sends JSON to backend  
- Displays preview (3D viewer)  

### 4.2 Backend Service
Responsibilities:
- Validate configuration  
- Apply rules  
- Compute derived parameters  
- Trigger CAD generation  

### 4.3 CAD Engine
Responsibilities:
- Load base CAD model  
- Modify parameters  
- Export CAD file (STEP)  

---

## 5. API Interface

POST /generate-cad  
Input: Config Schema  
Output: CAD file (STEP)

POST /compute-config  
Input: Config Schema  
Output:
{ module_count: number, module_length_cm: number }

---

## 6. Configuration Format (Example)

{
  use_case: "urban",
  dimensions: {
    width_cm: 100,
    height_cm: 150,
    length_cm: 250
  },
  structure: {
    cube_count: 2
  },
  mounting: {
    type: "none"
  },
  floor: {
    enabled: true,
    material: "wpc_dark"
  },
  walls: {
    enabled: true,
    material: "wpc_dark"
  },
  color: {
    ral: "7016"
  },
  door: {
    type: "sliding",
    material: "wpc_cedar"
  },
  features: []
}

---

## 7. Derived Configuration

Rules are applied to compute derived values.

Example:
{ module_count: 2, module_length_cm: 125 }

---

## 8. Data Flow

1. User configures product in frontend  
2. Frontend sends JSON to backend  
3. Backend validates input  
4. Backend applies rules  
5. Backend generates CAD  
6. CAD file returned to user  

---

## 9. External Systems

- Lovable (Frontend hosting)  
- GitHub (Source control)  
- GCP (Cloud Run, Cloud Build)  
- Fusion 360 (CAD engine)  

---

## 10. Environment Variables

- GCP_PROJECT_ID  
- CAD_API_KEY  
- STORAGE_BUCKET  

---

## 11. Constraints & Assumptions

- Configuration must be valid JSON  
- All CAD components must be predefined  
- Naming must match CAD components  

---

## 12. Open Questions

- How is Fusion 360 automated (API vs script)?  
- Where are CAD templates stored?  
- Is CAD generation synchronous or async?
- 