/**
 * Optimize pottery images for web delivery.
 * - JPEGs: resize to max 1920px on longest side, quality 85
 * - Logo PNG: resize to max 800px wide
 * Originals are safe in iCloud — this processes public/img/ in-place.
 */

import sharp from 'sharp';
import { readdir, stat, writeFile } from 'fs/promises';
import { join, extname, relative } from 'path';

const MAX_DIM     = 1920;
const JPEG_QUALITY = 85;
const DIRS        = ['public/img/pottery', 'public/img/logo.png'];

let total = 0, saved = 0;

async function optimizeJpeg(filePath) {
  const { size: before } = await stat(filePath);
  const img   = sharp(filePath);
  const meta  = await img.metadata();

  const buf = await img
    .resize(MAX_DIM, MAX_DIM, { fit: 'inside', withoutEnlargement: true })
    .jpeg({ quality: JPEG_QUALITY, mozjpeg: true })
    .toBuffer();

  if (buf.length < before) {
    await writeFile(filePath, buf);
    const after = buf.length;
    const newMeta = await sharp(buf).metadata();
    const pct = Math.round((1 - after / before) * 100);
    console.log(
      `  ✓ ${relative('', filePath)}: ${meta.width}x${meta.height} → ${newMeta.width}x${newMeta.height}` +
      `  ${kb(before)} → ${kb(after)} (-${pct}%)`
    );
    saved += before - after;
  } else {
    console.log(`  · ${relative('', filePath)}: already optimal, skipping`);
  }
  total += before;
}

async function optimizePng(filePath) {
  const { size: before } = await stat(filePath);
  const meta = await sharp(filePath).metadata();

  const buf = await sharp(filePath)
    .resize(800, null, { fit: 'inside', withoutEnlargement: true })
    .png({ compressionLevel: 9, adaptiveFiltering: true })
    .toBuffer();

  if (buf.length < before) {
    await writeFile(filePath, buf);
    const newMeta = await sharp(buf).metadata();
    const pct = Math.round((1 - buf.length / before) * 100);
    console.log(
      `  ✓ ${relative('', filePath)}: ${meta.width}x${meta.height} → ${newMeta.width}x${newMeta.height}` +
      `  ${kb(before)} → ${kb(buf.length)} (-${pct}%)`
    );
    saved += before - buf.length;
  }
  total += before;
}

async function processDir(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      await processDir(full);
    } else {
      const ext = extname(entry.name).toLowerCase();
      if (ext === '.jpg' || ext === '.jpeg') await optimizeJpeg(full);
      else if (ext === '.png') await optimizePng(full);
    }
  }
}

function kb(bytes) { return `${Math.round(bytes / 1024)}KB`; }

console.log('Optimizing images…\n');
await processDir('public/img/pottery');
await optimizePng('public/img/logo.png');
console.log(`\nDone. Saved ${Math.round(saved / 1024 / 1024 * 10) / 10}MB of ${Math.round(total / 1024 / 1024 * 10) / 10}MB total.`);
