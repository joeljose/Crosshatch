/**
 * Image processing — JS port of the notebook's pixel math.
 */

import { createCanvas, loadImage } from './utils.js';

const MAX_DIMENSION = 1200;
const HATCH_UNIT = 2100;

const TEXTURE_URLS = {
  right: 'textures/rightx.png',
  left: 'textures/leftx.png',
  horizontal: 'textures/horizontalx.png',
  vortex: 'textures/vortexx.png',
};

let textureCache = null;

/**
 * Load all hatch textures and convert to grayscale data.
 */
export async function loadTextures() {
  if (textureCache) return textureCache;

  const entries = Object.entries(TEXTURE_URLS);
  const results = await Promise.all(
    entries.map(async ([name, url]) => {
      const img = await loadImage(url);
      const c = createCanvas(img.width, img.height);
      const ctx = c.getContext('2d');
      ctx.drawImage(img, 0, 0);
      const imageData = ctx.getImageData(0, 0, c.width, c.height);
      const rgba = imageData.data;
      const gray = new Uint8Array(c.width * c.height);
      for (let i = 0; i < gray.length; i++) {
        const j = i * 4;
        gray[i] = Math.round(0.299 * rgba[j] + 0.587 * rgba[j + 1] + 0.114 * rgba[j + 2]);
      }
      return [name, { data: gray, width: c.width, height: c.height }];
    }),
  );

  textureCache = Object.fromEntries(results);
  return textureCache;
}

/**
 * High-quality canvas resize using step-down halving.
 * Halves dimensions repeatedly until close to target, then does a final resize.
 * This gives bilinear-interpolated quality comparable to Lanczos for downscaling.
 */
function canvasResize(srcCanvas, dstW, dstH) {
  let cur = srcCanvas;
  let curW = srcCanvas.width;
  let curH = srcCanvas.height;

  // Step down by halving until within 2x of target
  while (curW / 2 >= dstW && curH / 2 >= dstH) {
    const halfW = Math.floor(curW / 2);
    const halfH = Math.floor(curH / 2);
    const step = createCanvas(halfW, halfH);
    const ctx = step.getContext('2d');
    ctx.drawImage(cur, 0, 0, halfW, halfH);
    cur = step;
    curW = halfW;
    curH = halfH;
  }

  // Final resize to exact target
  const dst = createCanvas(dstW, dstH);
  const ctx = dst.getContext('2d');
  ctx.drawImage(cur, 0, 0, dstW, dstH);
  return dst;
}

/**
 * Put grayscale Uint8Array data onto a canvas as RGBA.
 */
function grayToCanvas(data, width, height) {
  const c = createCanvas(width, height);
  const ctx = c.getContext('2d');
  const imgData = ctx.createImageData(width, height);
  for (let i = 0; i < data.length; i++) {
    const j = i * 4;
    imgData.data[j] = data[i];
    imgData.data[j + 1] = data[i];
    imgData.data[j + 2] = data[i];
    imgData.data[j + 3] = 255;
  }
  ctx.putImageData(imgData, 0, 0);
  return c;
}

/**
 * Extract grayscale Uint8Array from a canvas (reads R channel).
 */
function canvasToGray(canvas) {
  const ctx = canvas.getContext('2d');
  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const gray = new Uint8Array(canvas.width * canvas.height);
  for (let i = 0; i < gray.length; i++) {
    gray[i] = imgData.data[i * 4];
  }
  return gray;
}

/**
 * Resize a grayscale image so its longest side is MAX_DIMENSION.
 * Returns { data, width, height }.
 */
export function resizeGrayscale(data, width, height) {
  const ratio = MAX_DIMENSION / Math.max(width, height);
  if (ratio >= 1) return { data, width, height };

  const newWidth = Math.trunc(ratio * width);
  const newHeight = Math.trunc(ratio * height);

  const srcCanvas = grayToCanvas(data, width, height);
  const dstCanvas = canvasResize(srcCanvas, newWidth, newHeight);
  return { data: canvasToGray(dstCanvas), width: newWidth, height: newHeight };
}

/**
 * Resize a mask (Uint8Array) to new dimensions.
 */
export function resizeMask(data, srcW, srcH, dstW, dstH) {
  const srcCanvas = grayToCanvas(data, srcW, srcH);
  const dstCanvas = canvasResize(srcCanvas, dstW, dstH);
  return canvasToGray(dstCanvas);
}

/**
 * Layer subject on white background using mask.
 * Where mask == 255 -> pixel, otherwise 255.
 */
export function layerOnWhite(gray, mask) {
  const out = new Uint8Array(gray.length);
  for (let i = 0; i < gray.length; i++) {
    out[i] = mask[i] === 255 ? gray[i] : 255;
  }
  return out;
}

/**
 * Calculate three threshold values that divide the tonal range into 4 equal zones.
 * Uses 2nd/98th percentile for robustness.
 */
export function calculateThresholds(data) {
  // Collect non-white pixels
  const pixels = [];
  for (let i = 0; i < data.length; i++) {
    if (data[i] < 255) pixels.push(data[i]);
  }

  if (pixels.length === 0) return [64, 128, 192];

  pixels.sort((a, b) => a - b);

  const percentile = (sorted, p) => {
    const idx = (p / 100) * (sorted.length - 1);
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    if (lo === hi) return sorted[lo];
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
  };

  const lo = percentile(pixels, 2);
  const hi = percentile(pixels, 98);
  const step = (hi - lo) / 4;
  return [
    Math.trunc(lo + step),
    Math.trunc(lo + 2 * step),
    Math.trunc(lo + 3 * step),
  ];
}

/**
 * Crop a texture to match the target dimensions.
 * right, left, horizontal: top-left crop
 * vortex: center crop
 */
export function cropTexture(texture, targetW, targetH, centerCrop = false) {
  const out = new Uint8Array(targetW * targetH);
  if (centerCrop) {
    const startY = Math.floor((texture.height - targetH) / 2);
    const startX = Math.floor((texture.width - targetW) / 2);
    for (let y = 0; y < targetH; y++) {
      for (let x = 0; x < targetW; x++) {
        out[y * targetW + x] = texture.data[(y + startY) * texture.width + (x + startX)];
      }
    }
  } else {
    for (let y = 0; y < targetH; y++) {
      for (let x = 0; x < targetW; x++) {
        out[y * targetW + x] = texture.data[y * texture.width + x];
      }
    }
  }
  return out;
}

/**
 * Apply a hatch layer: where layered < threshold, use texture; otherwise 255.
 */
export function applyHatch(layered, textureCropped, threshold) {
  const out = new Uint8Array(layered.length);
  for (let i = 0; i < layered.length; i++) {
    out[i] = layered[i] < threshold ? textureCropped[i] : 255;
  }
  return out;
}

/**
 * Blend three hatch layers with equal weight.
 * Uses Math.trunc to match Python's int() behavior.
 */
export function blendLayers(h1, h2, h3) {
  const out = new Uint8Array(h1.length);
  for (let i = 0; i < h1.length; i++) {
    out[i] = Math.trunc((h1[i] + h2[i] + h3[i]) / 3);
  }
  return out;
}
