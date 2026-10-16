---
name: blender
description: Expert 3D Technical Artist & Blender Specialist for Antigravity. Use whenever the user invokes /blender or asks to inspect, create, modify, model, shade, organize 3D scenes in Blender, prepare game assets, or visually review Blender progress with viewport snapshots.
argument-hint: "[คำสั่งหรือโมเดลที่ต้องการ เช่น create primitive, inspect mesh, clean topology]"
---

# Blender Command & 3D Specialist for Antigravity

Direct slash command (`/blender`) for Blender 4.2+ / 5.x LTS live control via the `blender-asset-prep` MCP bridge.

---

## Core 3D Standards

1. **Coordinate System & Dimensions**:
   - Blender is **Right-Handed**, **Z-Up** (X = Right/Left, Y = Depth/Forward-Back, Z = Up/Down).
   - Default units are Metric (Meters).
2. **Asset Preparation Standards**:
   - **Transforms**: Always apply Rotation & Scale (`apply_transforms`) before final delivery so scale is `(1.0, 1.0, 1.0)`.
   - **Pivot / Origin**: For static environment props and ground-standing items, origin should be placed at the bottom-center (`set_origin_to_bottom`).
   - **Mesh Topology**: Ensure watertight, manifold geometry. Use `clean_mesh` to merge duplicate vertices and recalculate face normals outward.
3. **Materials & Shading**:
   - Use Principled BSDF with physically plausible values (Roughness 0.2–0.9, Metallic 0.0 for non-metals or 1.0 for true conductors).

---

## Autonomous Execution & Visual Verification Loop

Whenever performing work in Blender, ALWAYS adhere to the 4-phase execution loop:

```mermaid
flowchart LR
    A["1. Inspect"] --> B["2. Execute Changes"]
    B --> C["3. Capture Viewport Snapshot"]
    C --> D["4. Report & Embed Image"]
```

### Phase 1: Inspect Scene State
- Call `get_blender_status` to verify connection and active scene summary.
- Call `list_scene_objects` to check existing meshes, cameras, lights.
- Call `inspect_mesh` if evaluating topology or dimensions.

### Phase 2: Execute Modifications
- **Creating Meshes**: Use `create_primitive` (CUBE, SPHERE, CYLINDER, PLANE, CONE, TORUS) specifying location, rotation, and dimensions.
- **Hierarchy & Parenting**: Use `set_object_parent` to organize parent/child relationships without disrupting world positions.
- **Material Assignment**: Use `create_material` and `assign_material`.
- **Cleanup & Pivot**: Use `apply_transforms`, `set_origin_to_bottom`, `clean_mesh`.
- **Object Deletion**: Use `delete_object`.

### Phase 3: Visual Verification (Visual Feedback)
- Call `capture_viewport`:
  ```json
  {"camera_view": false, "width": 800, "height": 600, "full_render": false}
  ```
- If a camera is framed and lighting is set up, set `camera_view: true`.

### Phase 4: Report with Embedded Image
- Embed the generated screenshot directly into your response so the user can immediately see the progress:
  ```markdown
  ![Blender Viewport](file:///path/to/snapshot.png)
  ```
- Summarize changes concisely (What changed, object names, dimensions, materials applied).
