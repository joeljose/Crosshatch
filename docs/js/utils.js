/**
 * Canvas and download helpers.
 */

/**
 * Create an offscreen canvas with the given dimensions.
 */
export function createCanvas(width, height) {
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  return c;
}

/**
 * Load an image file (File or Blob) into an HTMLImageElement.
 */
export function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };
    img.src = url;
  });
}

/**
 * Load an image from a URL into an HTMLImageElement.
 */
export function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
    img.src = url;
  });
}

/**
 * Get grayscale pixel data from an image as a Uint8Array (H*W).
 * Also returns { width, height }.
 */
export function imageToGrayscaleData(img) {
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
  return { data: gray, width: c.width, height: c.height };
}

/**
 * Get RGBA pixel data from an image.
 */
export function imageToRGBAData(img) {
  const c = createCanvas(img.width, img.height);
  const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0);
  return ctx.getImageData(0, 0, c.width, c.height);
}

/**
 * Draw grayscale Uint8Array data onto a canvas element.
 */
export function drawGrayscaleToCanvas(canvas, data, width, height) {
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  const imageData = ctx.createImageData(width, height);
  for (let i = 0; i < data.length; i++) {
    const j = i * 4;
    imageData.data[j] = data[i];
    imageData.data[j + 1] = data[i];
    imageData.data[j + 2] = data[i];
    imageData.data[j + 3] = 255;
  }
  ctx.putImageData(imageData, 0, 0);
}

/**
 * Draw an RGBA ImageData onto a canvas element (resized to fit).
 */
export function drawImageToCanvas(canvas, img) {
  canvas.width = img.width;
  canvas.height = img.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
}

/**
 * Trigger a file download from a canvas.
 */
export function downloadCanvas(canvas, filename, type = 'image/jpeg', quality = 0.92) {
  canvas.toBlob(
    (blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    },
    type,
    quality,
  );
}
