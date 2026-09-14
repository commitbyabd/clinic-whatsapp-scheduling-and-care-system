/* Generates right-sized copies of the site's photography and logo.

   The originals stay in place as the masters. The site shows portraits at
   38–350px, and decoding a 1254px image for a 150px circle costs ~6 MB of
   memory each; across the Our Team page that added up to ~90 MB of bitmaps
   to display ~4 MB worth of pixels. Under that pressure the browser was
   dropping the paint of whichever nurse portrait it reached last.

   Each size is roughly 2x its largest on-screen size, for high-density
   displays.

   Run after adding or replacing any portrait or the logo:
     npm run images:thumbs */

import { mkdir, readdir } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const AVIF = { quality: 60, effort: 4 };

/* ------------------------------------------------------------------ */
/* Portraits                                                           */
/* ------------------------------------------------------------------ */

const portraitJobs = [
  /* Nurse wall: 176px desktop at most, 122px on phones at 3x. */
  { dir: "public/images/pages/our-team/nurses", width: 400 },
  /* Doctor cards: up to ~350px wide on tablet. */
  { dir: "public/images/pages/our-team/doctors", width: 720 },
  /* Doctor faces reused as small avatars: 38px (Home hero), 52px (Who We Are). */
  { dir: "public/images/pages/our-team/doctors", width: 160 },
];

for (const { dir, width } of portraitJobs) {
  const outDir = path.join(dir, `w${width}`);
  await mkdir(outDir, { recursive: true });

  const files = (await readdir(dir)).filter((file) => file.endsWith(".avif"));

  for (const file of files) {
    const { size } = await sharp(path.join(dir, file))
      .resize({ width, withoutEnlargement: true })
      .avif(AVIF)
      .toFile(path.join(outDir, file));

    console.log(`${path.join(outDir, file)}  ${(size / 1024).toFixed(1)} KB`);
  }
}

/* ------------------------------------------------------------------ */
/* Logo                                                                */
/* ------------------------------------------------------------------ */

/* The master is a 2172x724 lockup: the marigold mark on the left, then the
   "Marigold Health" wordmark and "CLINIC & MEDICAL CENTRE" tagline in dark
   ink. It sits on the cream header as-is, but on the charcoal footer that
   ink would vanish — so the footer gets a variant with the lettering turned
   light and the mark left exactly as it is. */

const LOGO_MASTER = "public/images/logo.avif";
const LOGO_OUT = "public/images/logo";
const LOGO_WIDTH = 400; /* shown at ~126px wide, so 3x headroom */

/* First column of the lettering. The mark ends at column 518 and the
   wordmark starts at 569 in the master; this is the middle of that
   transparent gap. Re-measure if the master artwork changes. */
const LETTERING_STARTS_AT = 544;

const CREAM = [246, 241, 233]; /* --cream-base, as the old footer name */
const MUTED = [189, 180, 167]; /* --on-dark-muted */

const mix = (from, to, t) => from.map((c, i) => Math.round(c + (to[i] - c) * t));

const buildOnDarkLogo = async () => {
  const { data, info } = await sharp(LOGO_MASTER)
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  const { width, height, channels } = info;
  const out = Buffer.from(data);

  for (let y = 0; y < height; y += 1) {
    for (let x = LETTERING_STARTS_AT; x < width; x += 1) {
      const i = (y * width + x) * channels;
      if (out[i + 3] === 0) continue;

      /* Keep the hierarchy of the original: its near-black name becomes
         cream, and its lighter taupe tagline becomes the muted on-dark tone.
         Alpha is untouched, so the anti-aliased edges survive. */
      const luma = 0.299 * out[i] + 0.587 * out[i + 1] + 0.114 * out[i + 2];
      const t = Math.min(1, Math.max(0, (luma - 40) / 100));
      const [r, g, b] = mix(CREAM, MUTED, t);

      out[i] = r;
      out[i + 1] = g;
      out[i + 2] = b;
    }
  }

  return sharp(out, { raw: { width, height, channels } });
};

await mkdir(LOGO_OUT, { recursive: true });

const logoOutputs = [
  { name: "logo.avif", image: sharp(LOGO_MASTER) },
  { name: "logo-on-dark.avif", image: await buildOnDarkLogo() },
];

for (const { name, image } of logoOutputs) {
  const target = path.join(LOGO_OUT, name);
  const { size } = await image
    .resize({ width: LOGO_WIDTH, withoutEnlargement: true })
    .avif(AVIF)
    .toFile(target);

  console.log(`${target}  ${(size / 1024).toFixed(1)} KB`);
}
