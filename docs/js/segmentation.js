/**
 * Segmentation using ONNX Runtime Web with u2net_human_seg model.
 */

import { createCanvas } from './utils.js';
import { resizeMask } from './image-processing.js';

const MODEL_URL =
  'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx';
const CACHE_NAME = 'crosshatch-models-v1';
const INPUT_SIZE = 320;

// ImageNet normalization (matches rembg's preprocessing)
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

let session = null;

/**
 * Fetch the model with caching and progress reporting.
 * Returns an ArrayBuffer of the model.
 */
async function fetchModelWithProgress(onProgress) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(MODEL_URL);

  if (cached) {
    onProgress(1);
    return await cached.arrayBuffer();
  }

  const response = await fetch(MODEL_URL);
  if (!response.ok) throw new Error(`Model download failed: ${response.status}`);

  const contentLength = parseInt(response.headers.get('content-length') || '0', 10);
  const reader = response.body.getReader();
  const chunks = [];
  let received = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    if (contentLength > 0) {
      onProgress(received / contentLength);
    }
  }

  const blob = new Blob(chunks);

  // Cache for next time
  const cacheResponse = new Response(blob, {
    headers: { 'Content-Type': 'application/octet-stream' },
  });
  await cache.put(MODEL_URL, cacheResponse);

  return await blob.arrayBuffer();
}

/**
 * Load the ONNX model (downloads if needed, caches for reuse).
 * onProgress(fraction) called during download.
 */
export async function loadModel(onProgress = () => {}) {
  if (session) return session;

  const ort = await import('https://cdn.jsdelivr.net/npm/onnxruntime-web@1.21.0/+esm');

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

  const ort = await import('https://cdn.jsdelivr.net/npm/onnxruntime-web@1.21.0/+esm');

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
