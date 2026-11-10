# Studio media: template and presets for the Jalon app (Nov 10, 2026)

Every studio page in the app (Studio A, B, C, D) gets the same media set:

- **1 reel** (vertical video that loops at the top of the studio page)
- **4 or 5 photos** (4 required, the 5th optional)

Part 1 is the template: the slots and specs every studio follows. Part 2 is the preset for each studio: the exact
shots to film and photograph. The same data, ready for the code, is in `ops/studio-media/studio-media.ts`.

---

## Part 1: the template

### The reel

| | Spec |
|---|---|
| Format | Vertical 9:16, 1080 × 1920, 30 fps |
| Length | 15 s (12–20 s is fine). It loops, so the last frame should flow into the first. |
| File | `reel.mp4` (H.264, AAC), under 8 MB. Optional second copy `reel.webm` (VP9). |
| Poster | `reel-poster.jpg`, 1080 × 1920, a clean frame from the first second. Shown before the video loads. |
| Sound | The app plays it **muted** on autoplay. Nothing in it can depend on sound. Keep the room sound on the file for socials. |
| Text | **No burned-in text or prices in the app version.** The app writes the studio name, price and "Réserver" button over it, and prices change. A social version with text can be cut from the same footage. |
| Safe zone | Keep faces and gear inside the middle 1080 × 1420. The top 250 px and bottom 250 px are covered by the app's header and booking button. |

**The 5 beats every reel follows (15 s):**

| Time | Beat | What it shows |
|---|---|---|
| 0–2 s | Arrive | The door, the stairs or the hallway to the room. A light switches on. |
| 2–5 s | Reveal | The whole room in one slow move (push in or pan). |
| 5–10 s | In use | Someone working in the room: the thing you'd book it for. |
| 10–13 s | Signature detail | One close-up of what makes this room different. |
| 13–15 s | Settle | A wide, still frame to loop back on (same framing as the reveal if possible). |

### The photos

| Slot | Name | Required | Size | What it is |
|---|---|---|---|---|
| 1 | Cover | Yes | 2400 × 1350 (16:9) | The whole room, lights on, empty and tidy. Used on the studio card and as the page header on desktop. Must still work cropped to the centre 4:5. |
| 2 | In use | Yes | 1600 × 2000 (4:5) | Someone working in the room. |
| 3 | Signature gear | Yes | 1600 × 2000 (4:5) | Close-up of the room's main piece of gear. |
| 4 | Detail | Yes | 1600 × 2000 (4:5) | A second close-up: a second piece of gear, a texture, a light. |
| 5 | Atmosphere | Optional | 1600 × 2000 (4:5) | The mood shot: evening light, a wide from another angle, the view out. |

- Files: `photo-1-cover.jpg` to `photo-5-atmosphere.jpg`, JPG at quality 80, under 600 KB each. The app can convert
  them to WebP/AVIF.
- Same colour grade across all four studios, so the pages look like one place.
- Every photo needs alt text in French and English (it's in each preset below and in the code file).

### Where the files go

```
public/studios/studio-a/reel.mp4
public/studios/studio-a/reel-poster.jpg
public/studios/studio-a/photo-1-cover.jpg
public/studios/studio-a/photo-2-in-use.jpg
public/studios/studio-a/photo-3-signature.jpg
public/studios/studio-a/photo-4-detail.jpg
public/studios/studio-a/photo-5-atmosphere.jpg   (optional)
```

Same names for `studio-b`, `studio-c` and `studio-d`. The path can be swapped for Supabase Storage or a CDN URL in
the code file; the names stay the same.

### People in the shots (Quebec)

- Anyone recognisable needs **written, opt-in consent** for the app, the website and social media, asked
  separately (Civil Code art. 36, Law 25; see `docs/app-redesign-vision.md` section 5).
- Use the team or roster artists who have signed the consent annex. **No clients** unless they've signed it too.
- Hands, backs and silhouettes don't need it. They're the safe default for "in use" shots.
- Credit the photographer in the file's metadata.

---

## Part 2: the presets, studio by studio

### Studio A: recording room (ground floor)

What it sells: a tracking room with engineer (KJ), the mic collection, the Prophet Rev2 and the Apollo interfaces.

> ⚠ **Do not show the SSL console or the control room.** They're no longer part of the offer (see
> `docs/studio-pricing-and-projections.md`). Frame every shot in the tracking room.

**Reel (15 s)**

| Time | Shot |
|---|---|
| 0–2 s | Ground-floor hallway, the Studio A door opens, the room light comes on. |
| 2–5 s | Slow push into the tracking room: mic on its stand, headphones hanging, warm light. |
| 5–10 s | A vocalist at the mic, shot from behind or the side (or KJ setting the mic height). Cut in: hands on the Apollo. |
| 10–13 s | Close-up: fingers on the Prophet Rev2, its screen and lit knobs. |
| 13–15 s | Wide of the empty room, mic in the centre. Loops back to the push-in. |

**Photos**

| Slot | Shot | Alt text (FR / EN) |
|---|---|---|
| 1 Cover | The tracking room from the door, mic in the centre, lights on. | Studio A, salle d'enregistrement, micro au centre / Studio A recording room with a mic in the centre |
| 2 In use | A vocalist at the mic with headphones, from behind or the side, pop filter in frame. | Une voix s'enregistre au Studio A / A vocalist recording in Studio A |
| 3 Signature | The Prophet Rev2, three-quarter angle, knobs lit. | Synthétiseur Prophet Rev2 au Studio A / Prophet Rev2 synthesizer in Studio A |
| 4 Detail | The mic collection lined up, or a large-diaphragm mic close-up. | La collection de micros du Studio A / Studio A's microphone collection |
| 5 Atmosphere | Apollo meters glowing in a dark room. | Les vumètres de l'Apollo dans la pénombre / Apollo meters glowing in the dark |

---

### Studio B: self-serve membership studio (basement)

What it sells: a room you book with a membership and run yourself. Confirmed gear: Wagner upright piano, Alesis
88-key MIDI keyboard, Townsend Labs Sphere, Rode NT4 and M5 pairs, Apex 210 ribbon, Shure SM7B / Beta 57 / SM57,
UA Volt 8 Pre, Dynaudio LYD 48 monitors, video lighting, 50-inch TV.

**Reel (15 s)**

| Time | Shot |
|---|---|
| 0–2 s | Stairs down to the basement, a member's hand taps in / opens the door, lights come on. |
| 2–5 s | Pan across the room: the piano, the desk with the Dynaudio monitors, the TV. |
| 5–10 s | A member alone at the Wagner piano, a Rode mic pair above it. Cut: the same person at the Alesis keyboard and laptop. |
| 10–13 s | Close-up: hands on the Wagner keys. |
| 13–15 s | Wide of the room with the video lighting on. Loops back to the pan. |

**Photos**

| Slot | Shot | Alt text (FR / EN) |
|---|---|---|
| 1 Cover | The whole room: piano, desk, monitors, video lights on. | Studio B, studio autonome au sous-sol / Studio B, the self-serve basement studio |
| 2 In use | One member working alone at the desk or the piano (the "it's yours for the session" feeling). | Un membre en session au Studio B / A member in session in Studio B |
| 3 Signature | The Wagner upright with the Rode pair miking it. | Le piano droit Wagner du Studio B / Studio B's Wagner upright piano |
| 4 Detail | The Universal Audio Volt 8 Pre with the Shure SM7B, or the Townsend Sphere. | Interface UA Volt et micro Shure SM7B / UA Volt interface and Shure SM7B mic |
| 5 Atmosphere | The Dynaudio monitors and the 50-inch TV from the chair, lights low. | Le poste d'écoute du Studio B / Studio B's listening position |

---

### Studio C: content creation room (2nd floor)

What it sells: a white infinity wall (cyclorama) with lights for photo and video, self-serve or with an operator, plus
a membership.

**Reel (15 s)**

| Time | Shot |
|---|---|
| 0–2 s | Second-floor door opens onto the bright white wall. |
| 2–5 s | Slow pull back revealing the whole infinity wall and the light stands. |
| 5–10 s | A creator filming themselves on a phone on the wall, then the operator adjusting a light. Hard light, quick cuts. |
| 10–13 s | Close-up: the camera monitor showing the shot being made. |
| 13–15 s | The empty white wall, lights on. Loops back to the pull back. |

**Photos**

| Slot | Shot | Alt text (FR / EN) |
|---|---|---|
| 1 Cover | The full infinity wall, empty, all lights on. | Studio C, mur infini blanc / Studio C's white infinity wall |
| 2 In use | A creator or model on the wall, hard light, with the camera in the foreground. | Une séance photo au Studio C / A photo shoot in Studio C |
| 3 Signature | The lighting setup: key light and softbox from the side. | L'éclairage du Studio C / Studio C's lighting setup |
| 4 Detail | Camera on a tripod with the monitor showing the shot. | La caméra et l'écran de contrôle / The camera and its monitor |
| 5 Atmosphere | Overhead or wide shot of the team on the wall, everyone in black (from the shot list in `docs/app-redesign-vision.md`). | L'équipe sur le mur infini / The team on the infinity wall |

---

### Studio D: podcast room (3rd floor)

What it sells: a podcast studio with multicam, producer-run on weekdays and self-serve evenings and weekends, plus
12-episode seasons.

**Reel (15 s)**

| Time | Shot |
|---|---|
| 0–2 s | Third-floor door, the **ON AIR** light switches on. |
| 2–5 s | Slow push to the table: two mics facing each other, chairs, cameras. |
| 5–10 s | Two hosts talking and laughing at the table (wide), then a cut to the producer at the board. |
| 10–13 s | Close-up: the on-air light, or the camera feeds on the monitor in a multicam grid. |
| 13–15 s | Wide of the empty set, lights on. Loops back to the push. |

**Photos**

| Slot | Shot | Alt text (FR / EN) |
|---|---|---|
| 1 Cover | The full set from the main camera angle: table, two mics, lights on. | Studio D, plateau de balado / Studio D podcast set |
| 2 In use | Two hosts mid-conversation. | Un enregistrement de balado au Studio D / A podcast recording in Studio D |
| 3 Signature | The ON AIR light lit. | Le voyant « En ondes » du Studio D / Studio D's on-air light |
| 4 Detail | The podcast mics on boom arms, close. | Les micros de balado / The podcast mics |
| 5 Atmosphere | The multicam view: three camera angles on the monitor. | Les trois angles de caméra / The three camera angles |

---

## Shoot plan: one day for all four

1. **Morning, empty rooms:** all the covers (slot 1), signature and detail shots (slots 3 and 4), and every reel's
   reveal and settle beats. Go top to bottom: D, C, B, A.
2. **Afternoon, with people (consent signed):** all slot 2 shots and every reel's "in use" beat.
3. **Evening:** the atmosphere shots (slot 5), Studio A's Apollo meters in the dark, Studio D's on-air light.
4. Edit: one grade for everything, cut the four reels to 15 s, export the poster frames.

Checklist before the files go in the app:

- [ ] 4 reels, 9:16, about 15 s, under 8 MB, no burned-in text
- [ ] 4 poster frames
- [ ] 16 required photos (4 per studio), plus up to 4 optional
- [ ] No SSL or control room in any Studio A shot
- [ ] Consent on file for every recognisable person
- [ ] Alt text FR/EN checked
