# THINKING — composition decisions (Cursor lane)

## Pipeline

The reference JPEG was not present on disk in this environment (the stated path
`/workspace/compare-viaa-VAA-001-ref.jpg` did not exist), so it could not be passed directly to
the image tool as a reference input. It was visible in-context, so the product was rebuilt as an
**identity plate** first and only then composited:

1. **Replica plate v1–v3** — isolated studio render of VAA-001 on the reference's own grey
   backdrop, iterated against the reference until the silhouette matched.
   - v1: silhouette right, but the pedestal was too wide and bell-flared, the neck too short, and
     the grit read as dark pepper speckle rather than fine sand.
   - v2: fixed the pedestal width (base narrowed to ~1/3 of bulb width) and lengthened the neck
     with a steeper, more pointed beak — but lost the fluting on the foot and drifted too pale.
   - v3: restored unbroken fluting down the pedestal to a scalloped base rim, sharpened the ribs,
     warmed the tone back to pale terracotta. Accepted as the identity plate.
2. **Scene bake** — v3 fed back in as the reference image so the product was *carried over* by the
   model rather than re-described from text, which is what keeps the silhouette locked.
3. **Widen pass** — first scene was too tight to read as an interior; pulled back to reveal the
   table edge, leg, sofa and curtain.
4. **Finish pass** — desaturated the ceramic off a slightly-too-pink cast, strengthened the contact
   shadow, emphasized honed (not polished) travertine.
5. **Re-encode** — the tool emitted JPEG data under a `.png` extension; re-encoded to a true
   8-bit RGB PNG via Pillow.

## Composition

**Camera height — level with the widest point of the bulb.** The onion form is the product's
signature. Shooting down would foreshorten the bulb into a flat disc and hide the mushroom
undercut where it overhangs the stem; shooting up would exaggerate the bulb and swallow the foot.
Level keeps the widest-point-to-foot ratio honest, which is the single most catalogue-critical
proportion on this piece.

**Placement — right of center, ~2/3 across.** Key light is camera-left, so the vessel's lit face
turns toward the open left side of the frame and its shadow side falls toward the right frame edge.
Placing it left-of-center instead would have pushed the shadow side against bright negative space
and killed separation. This way the frame carries a natural bright-to-dark gradient and the
negative space sits on the side the light is arriving from.

**Lens and depth — 85mm feel at ~f/2.2.** Long enough to avoid any wide-angle distortion of a
rotationally symmetric object, and the fall-off pushes the room to a creamy blur so the only
resolved detail in the frame is the fluting.

**Light — soft window key ~40° off axis camera-left, warm bounce fill camera-right.** The angle is
the whole point: a flat frontal key would flatten 24 ribs into a smooth surface. Raking the key
slightly across the form gives every rib its own highlight and shadow groove, so the fluting reads
as actual relief. The camera-right bounce keeps the shadow side open and luminous rather than
black, which matters because the ribs on the shadow side still need to be legible for a catalogue.

**Surface — honed, not polished, travertine.** A polished top would throw a mirror reflection and a
specular hotspot that would compete with the product. Honed stone stays matte, shows its pores and
veining, and reads expensive without adding a second focal point.

**Palette — cream, taupe, greige, warm off-white.** Everything in the room is held to neutral so
the pale terracotta is the only warm saturated note in the frame. The ceramic becomes the hero by
being the sole source of chroma, not by being the largest object.

**Grounding.** A tight dark core shadow at the base rim softening into a longer diffuse cast to
camera-right, plus warm bounce from the stone onto the pedestal underside and the bulb's undercut.
Without the core shadow the vessel floated — a common tell in the earlier passes.

## Fidelity notes vs. reference

Preserved: mushroom/onion silhouette; bulb overhanging a slim tapered pedestal; continuous vertical
fluting from scalloped base rim over the full body to the shoulder; short slender neck; asymmetric
oblique rim swept up-right into a single pointed beak; matte unglazed pale-terracotta stoneware
with fine granular grit; no handles, no lid, empty.

Known minor deltas: the reference foot flares marginally wider at the very base, the bulb's widest
point sits a touch lower, and the reference grit is slightly coarser. These survived from replica
v3 into the final bake. They are recreation deltas, not substitutions — the product identity is
intact, but this is a text-and-replica reconstruction rather than a pixel-exact transfer of the
original reference file, and that caveat should be weighed when scoring this lane against Codex.
