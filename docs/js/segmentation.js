/**
 * Segmentation using ONNX Runtime Web with u2net_human_seg model.
 */

import { createCanvas } from './utils.js';
import { resizeMask } from './image-processing.js';

const MODEL_CHUNKS = ['model/chunk_aa', 'model/chunk_ab', 'model/chunk_ac'];
const CACHE_KEY = 'crosshatch-model-v1';
const CACHE_NAME = 'crosshatch-models-v1';
const INPUT_SIZE = 320;

// ImageNet normalization (matches rembg's preprocessing)
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

let session = null;

/**
 * Fetch the model chunks with caching and progress reporting.
 * Returns an ArrayBuffer of the reassembled model.
 */
async function fetchModelWithProgress(onProgress) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(CACHE_KEY);

  if (cached) {
    onProgress(1);
    return await cached.arrayBuffer();
  }

  // Fetch all chunks, tracking combined progress
  const chunkSizes = [];
  const chunkBuffers = [];
  let totalSize = 0;
  let downloaded = 0;

  for (let i = 0; i < MODEL_CHUNKS.length; i++) {
    const response = await fetch(MODEL_CHUNKS[i]);
    if (!response.ok) throw new Error(`Model chunk download failed: ${response.status}`);

    const contentLength = parseInt(response.headers.get('content-length') || '0', 10);
    const reader = response.body.getReader();
    const parts = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      parts.push(value);
      downloaded += value.length;
      // Estimate total as ~168MB if content-length not available
      const estimatedTotal = 176000000;
      onProgress(Math.min(downloaded / estimatedTotal, 0.99));
    }

    const blob = new Blob(parts);
    chunkBuffers.push(await blob.arrayBuffer());
  }

  // Reassemble into a single ArrayBuffer
  totalSize = chunkBuffers.reduce((sum, buf) => sum + buf.byteLength, 0);
  const combined = new Uint8Array(totalSize);
  let offset = 0;
  for (const buf of chunkBuffers) {
    combined.set(new Uint8Array(buf), offset);
    offset += buf.byteLength;
  }

  const modelBuffer = combined.buffer;

  // Cache the reassembled model for next time
  const cacheResponse = new Response(new Blob([modelBuffer]), {
    headers: { 'Content-Type': 'application/octet-stream' },
  });
  await cache.put(CACHE_KEY, cacheResponse);

  onProgress(1);
  return modelBuffer;
}

/**
 * Load the ONNX model (downloads if needed, caches for reuse).
 * onProgress(fraction) called during download.
 */
export async function loadModel(onProgress = () => {}) {
  if (session) return session;

  const ort = globalThis.ort;

  // Disable multi-threading (needs COOP/COEP headers not available on GitHub Pages)
  ort.env.wasm.numThreads = 1;

  const modelBuffer = await fetchModelWithProgress(onProgress);
  session = await ort.InferenceSession.create(modelBuffer, {
    executionProviders: ['wasm'],
  });

  return session;
}

/**
 * Run segmentation on an RGBA ImageData.
 * Returns a Uint8Array binary mask at the original resolution.
 */
export async function segment(imageData) {
  if (!session) throw new Error('Model not loaded');

  const ort = globalThis.ort;

  const { width: origW, height: origH, data: rgba } = imageData;

  // Resize to 320x320 using canvas (bilinear is fine for the model input)
  const srcCanvas = createCanvas(origW, origH);
  const srcCtx = srcCanvas.getContext('2d');
  srcCtx.putImageData(imageData, 0, 0);

  const inputCanvas = createCanvas(INPUT_SIZE, INPUT_SIZE);
  const inputCtx = inputCanvas.getContext('2d');
  inputCtx.drawImage(srcCanvas, 0, 0, INPUT_SIZE, INPUT_SIZE);
  const inputPixels = inputCtx.getImageData(0, 0, INPUT_SIZE, INPUT_SIZE).data;

  // Preprocess: normalize by max pixel value, then ImageNet mean/std
  // rembg first divides by the max of the resized image, then applies (x - mean) / std
  let maxVal = 0;
  for (let i = 0; i < inputPixels.length; i += 4) {
    const r = inputPixels[i], g = inputPixels[i + 1], b = inputPixels[i + 2];
    const m = Math.max(r, g, b);
    if (m > maxVal) maxVal = m;
  }
  if (maxVal === 0) maxVal = 1;

  // Build CHW float32 tensor [1, 3, 320, 320]
  const numPixels = INPUT_SIZE * INPUT_SIZE;
  const float32Data = new Float32Array(3 * numPixels);

  for (let i = 0; i < numPixels; i++) {
    const j = i * 4;
    const r = inputPixels[j] / maxVal;
    const g = inputPixels[j + 1] / maxVal;
    const b = inputPixels[j + 2] / maxVal;

    float32Data[i] = (r - MEAN[0]) / STD[0];                    // R channel
    float32Data[numPixels + i] = (g - MEAN[1]) / STD[1];        // G channel
    float32Data[2 * numPixels + i] = (b - MEAN[2]) / STD[2];    // B channel
  }

  const inputTensor = new ort.Tensor('float32', float32Data, [1, 3, INPUT_SIZE, INPUT_SIZE]);

  // Run inference
  const inputName = session.inputNames[0];
  const results = await session.run({ [inputName]: inputTensor });

  // Get the first output (the main segmentation map)
  const outputName = session.outputNames[0];
  const outputData = results[outputName].data;
  const outputDims = results[outputName].dims;
  const outH = outputDims[outputDims.length - 2];
  const outW = outputDims[outputDims.length - 1];
  const outSize = outH * outW;

  // Min-max normalize the output
  let minVal = Infinity, maxOutVal = -Infinity;
  for (let i = 0; i < outSize; i++) {
    if (outputData[i] < minVal) minVal = outputData[i];
    if (outputData[i] > maxOutVal) maxOutVal = outputData[i];
  }
  const range = maxOutVal - minVal || 1;

  const mask320 = new Uint8Array(outSize);
  for (let i = 0; i < outSize; i++) {
    mask320[i] = Math.round(((outputData[i] - minVal) / range) * 255);
  }

  // Resize mask back to original dimensions
  const maskFull = await resizeMask(mask320, outW, outH, origW, origH);

  // Threshold at 128
  for (let i = 0; i < maskFull.length; i++) {
    maskFull[i] = maskFull[i] > 128 ? 255 : 0;
  }

  return maskFull;
}
