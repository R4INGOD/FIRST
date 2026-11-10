// Studio media presets for the Jalon app (milestone-app).
// Every studio gets 1 reel (9:16 loop) and 4 or 5 photos (4 required, the 5th optional).
// Shot list and specs: docs/studio-media-presets.md
//
// To use in milestone-app: copy this file to src/lib/studio-media.ts, put the files under
// public/studios/<id>/ (or set STUDIO_MEDIA_BASE to a Supabase Storage / CDN URL), and match
// StudioId to the room keys in src/lib/catalog.ts.

export type StudioId = "studio-a" | "studio-b" | "studio-c" | "studio-d";
export type PhotoSlot = "cover" | "in-use" | "signature" | "detail" | "atmosphere";

export interface Bilingual { fr: string; en: string }

export interface StudioReel {
  src: string;          // reel.mp4: H.264, 1080x1920, ~15 s, < 8 MB, no burned-in text
  srcWebm?: string;     // optional reel.webm (VP9)
  poster: string;       // reel-poster.jpg, 1080x1920
  width: 1080;
  height: 1920;
  durationSec: number;
  // The app plays it muted, looped and inline.
  autoplay: true;
  muted: true;
  loop: true;
  playsInline: true;
}

export interface StudioPhoto {
  slot: PhotoSlot;
  src: string;
  width: number;
  height: number;
  required: boolean;
  alt: Bilingual;
}

export interface StudioMedia {
  id: StudioId;
  name: Bilingual;
  reel: StudioReel;
  photos: StudioPhoto[];   // 4 required + 1 optional, in display order
}

// ---------------------------------------------------------------------------
// Template: the same slots and specs for every studio
// ---------------------------------------------------------------------------

export const STUDIO_MEDIA_BASE = "/studios";

export const PHOTO_TEMPLATE: { slot: PhotoSlot; file: string; width: number; height: number; required: boolean }[] = [
  { slot: "cover",      file: "photo-1-cover.jpg",      width: 2400, height: 1350, required: true },
  { slot: "in-use",     file: "photo-2-in-use.jpg",     width: 1600, height: 2000, required: true },
  { slot: "signature",  file: "photo-3-signature.jpg",  width: 1600, height: 2000, required: true },
  { slot: "detail",     file: "photo-4-detail.jpg",     width: 1600, height: 2000, required: true },
  { slot: "atmosphere", file: "photo-5-atmosphere.jpg", width: 1600, height: 2000, required: false },
];

function reel(id: StudioId, durationSec = 15): StudioReel {
  const dir = `${STUDIO_MEDIA_BASE}/${id}`;
  return {
    src: `${dir}/reel.mp4`,
    srcWebm: `${dir}/reel.webm`,
    poster: `${dir}/reel-poster.jpg`,
    width: 1080,
    height: 1920,
    durationSec,
    autoplay: true,
    muted: true,
    loop: true,
    playsInline: true,
  };
}

function photos(id: StudioId, alts: Record<PhotoSlot, Bilingual>): StudioPhoto[] {
  return PHOTO_TEMPLATE.map((t) => ({
    slot: t.slot,
    src: `${STUDIO_MEDIA_BASE}/${id}/${t.file}`,
    width: t.width,
    height: t.height,
    required: t.required,
    alt: alts[t.slot],
  }));
}

// ---------------------------------------------------------------------------
// Presets: one per studio
// ---------------------------------------------------------------------------

export const STUDIO_MEDIA: Record<StudioId, StudioMedia> = {
  // Recording room, ground floor. No SSL console or control room in any shot.
  "studio-a": {
    id: "studio-a",
    name: { fr: "Studio A · Salle d'enregistrement", en: "Studio A · Recording room" },
    reel: reel("studio-a"),
    photos: photos("studio-a", {
      cover:      { fr: "Studio A, salle d'enregistrement, micro au centre", en: "Studio A recording room with a mic in the centre" },
      "in-use":   { fr: "Une voix s'enregistre au Studio A", en: "A vocalist recording in Studio A" },
      signature:  { fr: "Synthétiseur Prophet Rev2 au Studio A", en: "Prophet Rev2 synthesizer in Studio A" },
      detail:     { fr: "La collection de micros du Studio A", en: "Studio A's microphone collection" },
      atmosphere: { fr: "Les vumètres de l'Apollo dans la pénombre", en: "Apollo meters glowing in the dark" },
    }),
  },

  // Self-serve membership studio, basement.
  "studio-b": {
    id: "studio-b",
    name: { fr: "Studio B · Studio autonome", en: "Studio B · Self-serve studio" },
    reel: reel("studio-b"),
    photos: photos("studio-b", {
      cover:      { fr: "Studio B, studio autonome au sous-sol", en: "Studio B, the self-serve basement studio" },
      "in-use":   { fr: "Un membre en session au Studio B", en: "A member in session in Studio B" },
      signature:  { fr: "Le piano droit Wagner du Studio B", en: "Studio B's Wagner upright piano" },
      detail:     { fr: "Interface UA Volt et micro Shure SM7B", en: "UA Volt interface and Shure SM7B mic" },
      atmosphere: { fr: "Le poste d'écoute du Studio B", en: "Studio B's listening position" },
    }),
  },

  // Content creation room with the infinity wall, 2nd floor.
  "studio-c": {
    id: "studio-c",
    name: { fr: "Studio C · Création de contenu", en: "Studio C · Content creation" },
    reel: reel("studio-c"),
    photos: photos("studio-c", {
      cover:      { fr: "Studio C, mur infini blanc", en: "Studio C's white infinity wall" },
      "in-use":   { fr: "Une séance photo au Studio C", en: "A photo shoot in Studio C" },
      signature:  { fr: "L'éclairage du Studio C", en: "Studio C's lighting setup" },
      detail:     { fr: "La caméra et l'écran de contrôle", en: "The camera and its monitor" },
      atmosphere: { fr: "L'équipe sur le mur infini", en: "The team on the infinity wall" },
    }),
  },

  // Podcast room, 3rd floor.
  "studio-d": {
    id: "studio-d",
    name: { fr: "Studio D · Balado", en: "Studio D · Podcast" },
    reel: reel("studio-d"),
    photos: photos("studio-d", {
      cover:      { fr: "Studio D, plateau de balado", en: "Studio D podcast set" },
      "in-use":   { fr: "Un enregistrement de balado au Studio D", en: "A podcast recording in Studio D" },
      signature:  { fr: "Le voyant « En ondes » du Studio D", en: "Studio D's on-air light" },
      detail:     { fr: "Les micros de balado", en: "The podcast mics" },
      atmosphere: { fr: "Les trois angles de caméra", en: "The three camera angles" },
    }),
  },
};

// Photos to show for a studio. Pass the slots whose files exist so a missing optional
// 5th photo is skipped instead of rendering a broken image.
export function studioPhotos(id: StudioId, available?: Set<PhotoSlot>): StudioPhoto[] {
  const all = STUDIO_MEDIA[id].photos;
  return available ? all.filter((p) => p.required || available.has(p.slot)) : all.filter((p) => p.required);
}

export function altText(photo: StudioPhoto, locale: "fr" | "en"): string {
  return photo.alt[locale];
}
