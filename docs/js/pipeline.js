/**
 * Crosshatch processing pipeline — orchestrates all steps with progress.
 */

import { imageToGrayscaleData, imageToRGBAData } from './utils.js';
import { loadModel, segment } from './segmentation.js';
import {
  loadTextures,
  resizeGrayscale,
  resizeMask,
  layerOnWhite,
  calculateThresholds,
  cropTexture,
  applyHatch,
  blendLayers,
} from './image-processing.js';

/**
 * Run the full crosshatch pipeline.
 *
 * @param {HTMLImageElement} img — the input image
 * @param {string} style — 'horizontal' or 'vortex'
 * @param {function} onProgress — callback(fraction, stepDescription)
 * @returns {{ data: Uint8Array, width: number, height: number }}
 */
export async function process(img, style = 'horizontal', onProgress = () => {}) {
  // Step 1: Load model
  onProgress(0, 'Loading segmentation model...');
  await loadModel((fraction) => {
    onProgress(fraction * 0.3, 'Downloading segmentation model...');
  });
  onProgress(0.3, 'Model ready');

  // Step 2: Load textures
  onProgress(0.32, 'Loading hatch textures...');
  const textures = await loadTextures();

  // Step 3: Segment
  onProgress(0.35, 'Segmenting subject...');
  const rgbaData = imageToRGBAData(img);
  const mask = await segment(rgbaData);

  // Step 4: Convert to grayscale
  onProgress(0.55, 'Converting to grayscale...');
  const { data: grayData, width: origW, height: origH } = imageToGrayscaleData(img);

  // Step 5: Resize
  onProgress(0.6, 'Resizing image...');
  const resized = resizeGrayscale(grayData, origW, origH);
  const { data: grayResized, width: newW, height: newH } = resized;

  // Resize mask to match
  const maskResized = await resizeMask(mask, origW, origH, newW, newH);

  // Re-threshold mask after resize (canvas may introduce intermediate values)
  for (let i = 0; i < maskResized.length; i++) {
    maskResized[i] = maskResized[i] > 128 ? 255 : 0;
  }

  // Step 6: Layer on white
  onProgress(0.65, 'Layering on white background...');
  const layered = layerOnWhite(grayResized, maskResized);

  // Step 7: Calculate thresholds
  onProgress(0.7, 'Analyzing tonal range...');
  const [thresh1, thresh2, thresh3] = calculateThresholds(layered);

  // Step 8: Crop textures
  onProgress(0.75, 'Preparing hatch textures...');
  const rightCrop = cropTexture(textures.right, newW, newH, false);
  const leftCrop = cropTexture(textures.left, newW, newH, false);
  const thirdTexture = style === 'vortex' ? textures.vortex : textures.horizontal;
  const thirdCrop = cropTexture(thirdTexture, newW, newH, style === 'vortex');

  // Step 9: Apply hatching
  onProgress(0.8, 'Applying hatch patterns...');
  const hatch1 = applyHatch(layered, rightCrop, thresh1);
  const hatch2 = applyHatch(layered, leftCrop, thresh2);
  const hatch3 = applyHatch(layered, thirdCrop, thresh3);

  // Step 10: Blend
  onProgress(0.9, 'Blending layers...');
  const result = blendLayers(hatch1, hatch2, hatch3);

  onProgress(1, 'Done!');
  return { data: result, width: newW, height: newH };
}
