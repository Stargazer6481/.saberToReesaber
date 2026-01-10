import json
import base64
from pathlib import Path
import sys

try:
    import UnityPy
    from UnityPy.enums import ClassIDType
except ImportError:
    print("[ERROR] UnityPy not installed. Run: pip install UnityPy")
    sys.exit(1)

# ------------------ CONFIG ------------------

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
OUTPUT_GEO = OUTPUT_DIR / "CustomGeometry"
OUTPUT_TEX = OUTPUT_DIR / "CustomTextures"
OUTPUT_PRESETS = OUTPUT_DIR / "Presets"

# ------------------ SETUP ------------------

for folder in [OUTPUT_DIR, OUTPUT_GEO, OUTPUT_TEX, OUTPUT_PRESETS]:
    folder.mkdir(parents=True, exist_ok=True)

# ------------------ DEBUG HELPERS ------------------

def log(msg):
    print(f"[INFO] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")
    sys.exit(1)

# ------------------ FIND SABER FILE ------------------

saber_files = list(INPUT_DIR.glob("*.saber"))
if not saber_files:
    error("No .saber file found in input/ folder. Place your .saber file there.")

saber_file = saber_files[0]
saber_name = saber_file.stem
log(f"Found .saber file: {saber_file.name}")

# ------------------ LOAD ASSETBUNDLE ------------------

log("Loading AssetBundle...")
try:
    env = UnityPy.load(str(saber_file))
except Exception as e:
    error(f"Failed to load .saber file: {e}")

# ------------------ EXTRACT MESHES ------------------

log("Extracting meshes...")
mesh_data = []

for obj in env.objects:
    if obj.type.name == "Mesh":
        try:
            data = obj.read()
            mesh_name = data.name if hasattr(data, 'name') and data.name else f"mesh_{obj.path_id}"
            
            # Sanitize filename but keep it simple
            mesh_name_clean = "".join(c for c in mesh_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not mesh_name_clean:
                mesh_name_clean = f"mesh_{obj.path_id}"
            
            # Export mesh as OBJ
            try:
                obj_data = data.export()
                if obj_data and len(obj_data) > 0:
                    # Convert string to bytes if needed
                    if isinstance(obj_data, str):
                        obj_bytes = obj_data.encode('utf-8')
                    else:
                        obj_bytes = obj_data
                    
                    # Save OBJ file to disk
                    obj_file = OUTPUT_GEO / f"{mesh_name_clean}.obj"
                    with open(obj_file, 'wb') as f:
                        f.write(obj_bytes)
                    
                    # Also store base64 for JSON (even though we might not use it)
                    obj_base64 = base64.b64encode(obj_bytes).decode('utf-8')
                    mesh_data.append({
                        "name": mesh_name_clean,
                        "filename": f"{mesh_name_clean}.obj",
                        "data": obj_base64,
                        "original_name": mesh_name
                    })
                    log(f"Extracted mesh: {mesh_name_clean}.obj ({len(obj_bytes)} bytes)")
                else:
                    warn(f"Empty mesh export for: {mesh_name_clean}")
            except Exception as export_err:
                warn(f"Failed to export mesh '{mesh_name_clean}': {export_err}")
        except Exception as e:
            warn(f"Failed to process mesh object: {e}")

# ------------------ EXTRACT TEXTURES ------------------

log("Extracting textures...")
texture_data = []

for obj in env.objects:
    if obj.type.name == "Texture2D":
        try:
            data = obj.read()
            tex_name = data.name if hasattr(data, 'name') and data.name else f"texture_{obj.path_id}"
            
            # Sanitize filename but keep original for reference
            tex_name_clean = "".join(c for c in tex_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not tex_name_clean:
                tex_name_clean = f"texture_{obj.path_id}"
            
            # Export texture
            try:
                img = data.image
                from io import BytesIO
                
                # Save PNG file to disk
                tex_file = OUTPUT_TEX / f"{tex_name_clean}.png"
                img.save(tex_file)
                
                # Also create base64 for JSON
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                png_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                texture_data.append({
                    "name": tex_name_clean,
                    "filename": f"{tex_name_clean}.png",
                    "data": png_base64,
                    "original_name": tex_name
                })
                log(f"Extracted texture: {tex_name_clean}.png ({buffer.tell()} bytes)")
            except Exception as export_err:
                warn(f"Failed to export texture '{tex_name_clean}': {export_err}")
        except Exception as e:
            warn(f"Failed to process texture object: {e}")

# ------------------ EXTRACT SPRITES ------------------

log("Extracting sprites (if any)...")

for obj in env.objects:
    if obj.type.name == "Sprite":
        try:
            data = obj.read()
            sprite_name = data.name if hasattr(data, 'name') and data.name else f"sprite_{obj.path_id}"
            
            # Sanitize filename
            sprite_name_clean = "".join(c for c in sprite_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not sprite_name_clean:
                sprite_name_clean = f"sprite_{obj.path_id}"
            
            # Export sprite
            try:
                img = data.image
                from io import BytesIO
                
                # Save PNG file to disk
                tex_file = OUTPUT_TEX / f"{sprite_name_clean}.png"
                img.save(tex_file)
                
                # Also create base64 for JSON
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                png_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                texture_data.append({
                    "name": sprite_name_clean,
                    "filename": f"{sprite_name_clean}.png",
                    "data": png_base64,
                    "original_name": sprite_name
                })
                log(f"Extracted sprite: {sprite_name_clean}.png ({buffer.tell()} bytes)")
            except Exception as export_err:
                warn(f"Failed to export sprite '{sprite_name_clean}': {export_err}")
        except Exception as e:
            warn(f"Failed to process sprite object: {e}")

# ------------------ SUMMARY ------------------

log(f"\nExtraction complete:")
log(f"  Meshes: {len(mesh_data)}")
log(f"  Textures: {len(texture_data)}")

if not mesh_data:
    warn("Warning: No meshes extracted. Preset will be empty.")

# ------------------ CATEGORIZE MESHES ------------------

def categorize_mesh(name):
    """Determine if mesh is hilt or blade based on name"""
    name_lower = name.lower()
    
    # Hilt keywords
    if any(k in name_lower for k in ["hilt", "handle", "grip", "guard", "pommel", "emitter"]):
        return "hilt"
    
    # Blade keywords
    if any(k in name_lower for k in ["blade", "beam", "glow", "laser"]):
        return "blade"
    
    # Default to hilt for unknown
    return "hilt"

# ------------------ GENERATE PRESET ------------------

# Pick first texture for trail if available
trail_texture = texture_data[0]["filename"] if texture_data else ""

preset = {
    "ModVersion": "0.3.17",
    "Version": 1,
    "RootSettings": {
        "Type": 0
    },
    "LocalTransform": {
        "Position": {"x": 0.0, "y": 0.0, "z": 0.0},
        "Rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
        "Scale": {"x": 1.0, "y": 1.0, "z": 1.0}
    },
    "Modules": [],
    "BinaryAssets": {
        "Textures": [],
        "Geometry": []
    }
}

# Add trail module first (like in the example)
preset["Modules"].append({
    "ModuleId": "reezonate.simple-trail",
    "Version": 1,
    "Config": {
        "MeshSettings": {
            "TrailLength": 0.3,
            "HorizontalResolution": 4,
            "VerticalResolution": 60
        },
        "MaterialSettings": {
            "trailType": 0,
            "materialType": 0,
            "mappingType": 0,
            "offset": 1.0,
            "width": 0.03,
            "distortionMultiplier": 1.0,
            "generalSettings": {
                "customTextureId": trail_texture,
                "opacityTextureId": trail_texture,
                "animationLayout": {
                    "totalFrames": 1,
                    "framesPerRow": 1,
                    "framesPerColumn": 1,
                    "frameDuration": 1.0
                },
                "tilingLayout": {"x": 1.0, "y": 1.0, "z": 0.0, "w": 0.0},
                "uvScroll": {"x": 0.0, "y": 0.0},
                "blendingMode": 0,
                "alwaysOnTop": False,
                "renderQueue": 3000
            },
            "maskSettings": {
                "mainMaskResolution": 128,
                "driversMaskResolution": 32,
                "lengthMappings": {
                    "colorOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}]
                    },
                    "alphaOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "scaleOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "valueFrom": 0.0,
                    "valueTo": 1.0
                },
                "widthMappings": {
                    "colorOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}]
                    },
                    "alphaOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "scaleOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "valueFrom": 0.0,
                    "valueTo": 1.0
                },
                "driversSampleMode": 0,
                "viewingAngleMappings": {
                    "colorOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}]
                    },
                    "alphaOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "scaleOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "valueFrom": 0.0,
                    "valueTo": 1.0
                },
                "surfaceAngleMappings": {
                    "colorOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}]
                    },
                    "alphaOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "scaleOverValue": {
                        "interpolationType": 0,
                        "controlPoints": [{"time": 0.0, "value": 1.0}]
                    },
                    "valueFrom": 0.0,
                    "valueTo": 1.0
                },
                "drivers": []
            }
        },
        "Enabled": True,
        "Name": "Trail",
        "LocalTransform": {
            "Position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "Rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
            "Scale": {"x": 1.0, "y": 1.0, "z": 1.0}
        },
        "ForceColorOverride": False,
        "ColorOverride": {
            "type": 0,
            "hue": 0.0,
            "saturation": 1.0,
            "value": 1.0,
            "hueShiftPerSecond": 0.0,
            "fakeGlowMultiplier": 1.0,
            "colorSource": 0
        }
    },
    "Children": []
})

# Add each mesh as a custom-model module (directly in Modules, not in containers)
for mesh in mesh_data:
    module = {
        "ModuleId": "reezonate.custom-model",
        "Version": 1,
        "Config": {
            "MeshSettings": {
                "modelId": mesh["filename"],
                "scale": 1.0,
                "flipNormals": False,
                "mirrorX": False,
                "mirrorY": False,
                "mirrorZ": False
            },
            "MaterialSettings": {
                "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                "reflectionColor": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                "envLightColor": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                "opacity": 1.0,
                "fresnelPower": 5.0,
                "metallic": 0.0,
                "roughness": 0.0,
                "envLightIntensity": 1.0,
                "reflectionIntensity": 1.0,
                "normalMapIntensity": 1.0,
                "sceneReflections": False,
                "sceneLights": False,
                "renderQueue": 2990,
                "cullMode": 0,
                "depthWrite": True,
                "maskSettings": {
                    "driversMaskResolution": 32,
                    "driversSampleMode": 0,
                    "viewingAngleMappings": {
                        "colorOverValue": {
                            "interpolationType": 0,
                            "controlPoints": [{"time": 0.0, "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}]
                        },
                        "alphaOverValue": {
                            "interpolationType": 0,
                            "controlPoints": [{"time": 0.0, "value": 1.0}]
                        },
                        "scaleOverValue": {
                            "interpolationType": 0,
                            "controlPoints": [{"time": 0.0, "value": 1.0}]
                        },
                        "valueFrom": 0.0,
                        "valueTo": 1.0
                    },
                    "surfaceAngleMappings": {
                        "colorOverValue": {
                            "interpolationType": 0,
                            "controlPoints": [{"time": 0.0, "value": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}}]
                        },
                        "alphaOverValue": {
                            "interpolationType": 0,
                            "controlPoints": [{"time": 0.0, "value": 1.0}]
                        },
                        "scaleOverValue": {
                            "interpolationType": 0,
                            "controlPoints": [{"time": 0.0, "value": 1.0}]
                        },
                        "valueFrom": 0.0,
                        "valueTo": 1.0
                    },
                    "drivers": []
                }
            },
            "TexturesSettings": {
                "animationLayout": {
                    "totalFrames": 1,
                    "framesPerRow": 1,
                    "framesPerColumn": 1,
                    "frameDuration": 1.0
                },
                "tilingLayout": {"x": 1.0, "y": 1.0, "z": 0.0, "w": 0.0},
                "uvScroll": {"x": 0.0, "y": 0.0}
            },
            "Enabled": True,
            "Name": "Custom Model",  # Generic name like in the example
            "LocalTransform": {
                "Position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "Rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "Scale": {"x": 1.0, "y": 1.0, "z": 1.0}
            },
            "ForceColorOverride": False,
            "ColorOverride": {
                "type": 0,
                "hue": 0.0,
                "saturation": 1.0,
                "value": 1.0,
                "hueShiftPerSecond": 0.0,
                "fakeGlowMultiplier": 1.0,
                "colorSource": 0
            }
        },
        "Children": []
    }
    
    # Add directly to preset modules
    preset["Modules"].append(module)
    log(f"Added module for '{mesh['name']}'")
    
    # Add to BinaryAssets
    preset["BinaryAssets"]["Geometry"].append({
        "AssetName": mesh["filename"],
        "Data": mesh["data"]
    })

# Add textures to BinaryAssets
for texture in texture_data:
    preset["BinaryAssets"]["Textures"].append({
        "AssetName": texture["filename"],
        "Data": texture["data"]
    })

# Save preset
preset_file = OUTPUT_PRESETS / f"{saber_name}.json"
try:
    with open(preset_file, "w", encoding="utf-8") as f:
        json.dump(preset, f, indent=2)
    log(f"\nPreset generated: {preset_file}")
except Exception as e:
    error(f"Failed to write preset: {e}")

log("\n✅ Conversion complete!")
log(f"Preset file: {preset_file}")
log(f"\nCopy the entire '{OUTPUT_DIR.name}/' folder to:")
log(f"  Beat Saber/UserData/ReeSabers/")
log(f"\nExtracted:")
log(f"  - {len(mesh_data)} mesh(es) → CustomGeometry/")
log(f"  - {len(texture_data)} texture(s) → CustomTextures/")
log(f"  - 1 preset → Presets/")
log(f"\nNote: Adjust positions, rotations, scales, and materials in-game as needed.")