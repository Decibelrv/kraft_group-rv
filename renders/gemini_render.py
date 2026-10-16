# Photoreal kitchen render via Gemini image models (Nano Banana).
# Usage (from repo root): python3 renders/gemini_render.py [model] [out.png]
# Needs x-goog-api-key on requests (injected by the proxy here) and a billed Gemini API project.
import base64, json, sys, urllib.request
model = sys.argv[1] if len(sys.argv) > 1 else "gemini-3-pro-image"
out = sys.argv[2] if len(sys.argv) > 2 else "renders/kitchen-render-photo.png"
img = base64.b64encode(open('renders/kitchen-render.png','rb').read()).decode()
prompt = """Turn this 3D kitchen visualization into a photorealistic interior photograph. STRICTLY preserve the exact layout, camera position, perspective, framing, proportions and geometry of every cabinet, door split, panel, appliance, wall, pier, ceiling and floor — do not add, remove, move or resize any elements.
Materials:
- All cabinet fronts: white high-gloss acrylic with crisp reflections of the room and soft light falloff.
- Countertop: black natural stone (Nero Absolute look), polished, with subtle sparkle; same thickness and the corner return as shown.
- Black recessed Gola handle-less profiles (black anodized aluminium) exactly where the black horizontal lines are, and the black plinths.
- Left tall column: built-in black glass oven at eye level, and a built-in black microwave directly above it, flush in the column.
- Other appliances integrated: flush black induction hob, panel-ready dishwasher hidden behind white fronts, integrated fridge in the tall columns on the right, slim integrated hood under the upper cabinets.
- At the end of the right tall run: a full-height glass display cabinet with tinted graphite glass door in a thin black aluminium frame, glass shelves with glassware softly visible inside, faint interior LED.
- Keep the black-and-white patterned cement tile backsplash, black matte faucet and undermount black sink, small plant, wooden board.
- Warm-neutral greige walls, dark grey ceiling with recessed downlights, large-format light grey porcelain floor tiles with soft reflections, warm LED strip under upper cabinets.
Lighting: natural daylight plus downlights, soft realistic shadows, global illumination, ambient occlusion in gaps. Shot on a full-frame camera, architectural interior photography, sharp, high detail, 3:2 landscape."""
body = {"contents":[{"parts":[{"inline_data":{"mime_type":"image/png","data":img}},{"text":prompt}]}],
        "generationConfig":{"responseModalities":["IMAGE"],"imageConfig":{"aspectRatio":"3:2","imageSize":"2K"}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
r = json.load(urllib.request.urlopen(req, timeout=300))
for p in r["candidates"][0]["content"]["parts"]:
    d = p.get("inlineData") or p.get("inline_data")
    if d:
        open(out,'wb').write(base64.b64decode(d["data"])); print("saved", out, d.get("mimeType")); break
    else: print(p.get("text","")[:300])
