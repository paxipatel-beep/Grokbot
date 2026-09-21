# Composition notes — `led-lifestyle.png`

Photoreal warm-minimal luxury living-room lifestyle shot. Hero is a coiled warm amber LED
strip on a travertine side table.

Native image generation **was available** on the agent VM (Cursor's built-in image generation
tool), so no fallback approach was needed. The generator returned JPEG bytes under a `.png`
name, so the delivered file was re-encoded losslessly to true PNG (`ffmpeg`, `rgb24`,
max compression) — the committed file is a real 1152×864 8-bit RGB PNG.

## Camera

- **85mm prime at f/2.0.** Long enough to compress the room and keep the background from
  competing, wide enough aperture that only the hero stays sharp.
- **Height ~75cm, seated eye level, angled gently down.** This is the decision the whole frame
  hangs on: shot level with the tabletop the coil collapses into a flat line and loses its
  spiral; from above it becomes a flat graphic circle and the room disappears. The gentle
  downward tilt renders the coil as a soft ellipse — the loops read individually while the room
  still reads as a room.
- **Three-quarter angle to the table** so the top surface and one side face are both visible.
  Two planes of travertine at different light angles is what sells the stone as a solid block
  rather than a texture swatch.
- **Focus locked on the near arc of the coil**, with the far arc already softening. Foreground
  blur on the table's front edge adds a second depth cue behind the subject-to-background one.

## Lighting

- **Single large off-frame window, camera-left, as key.** Broad and diffuse with low-contrast
  falloff and long soft shadows travelling right. One believable source keeps it editorial
  rather than product-lit.
- **The LED coil is its own practical.** It is the only emissive object, throwing a short amber
  gradient pool onto the stone and a faint warm rim along the table edge. The subject lighting
  itself is what earns the shot its focal point, so no accent light was added.
- **Ambient fill kept cool and neutral.** The amber only reads as warm by contrast; warming
  the whole frame would flatten the hero into the beige palette.
- **Raking key across the tabletop** so the travertine's pores catch edge shadow. Light arriving
  along the surface rather than down onto it is what makes the pitting legible.

## Materials

- **Honed travertine** side table — vuggy, open-pored, cream-beige. Chosen because its texture
  rewards the raking light and its warmth sits under the amber without clashing.
- **Oatmeal bouclé sofa** behind and right. Its nubbly loops break into pleasant bokeh instead
  of the mush a flat fabric would give.
- **Hand-troweled lime plaster wall**, warm off-white, subtly mottled — an unfocused backdrop
  with just enough tonal variation to avoid looking like a grey card.
- **Brushed brass** floor-lamp stem: one restrained vertical and the only metallic specular,
  placed far back so it stays a soft accent.
- **Low-pile ivory wool rug on pale oak plank flooring**, plus a single matte bone-white
  ceramic vessel for scale.
- **Palette deliberately tonal** — cream, taupe, sand, warm grey, pale oak — so the amber is the
  only saturated note in the frame.

## Constraints honoured

No people, no hands, no pets, no logos or branding, no text or lettering anywhere, no caption,
no watermark or signature, no borders or UI overlay.
