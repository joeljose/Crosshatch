/**
 * UI wiring — drag-and-drop, file picker, process, download.
 */

import { loadImageFromFile, drawImageToCanvas, drawGrayscaleToCanvas, downloadCanvas } from './utils.js';
import { process } from './pipeline.js';

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const controls = document.getElementById('controls');
const styleSelect = document.getElementById('style-select');
const processBtn = document.getElementById('process-btn');
const progressSection = document.getElementById('progress-section');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const resultsSection = document.getElementById('results');
const originalCanvas = document.getElementById('original-canvas');
const resultCanvas = document.getElementById('result-canvas');
const downloadJpg = document.getElementById('download-jpg');
const downloadPng = document.getElementById('download-png');
const tryAnother = document.getElementById('try-another');

let currentImage = null;
const dropZoneInitialHTML = dropZone.querySelector('.drop-zone-content').innerHTML;

// --- Drop zone ---

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    fileInput.click();
  }
});

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    handleFile(file);
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) {
    handleFile(fileInput.files[0]);
  }
});

// --- File handling ---

async function handleFile(file) {
  try {
    currentImage = await loadImageFromFile(file);
    controls.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    progressSection.classList.add('hidden');

    // Update drop zone to show selected file
    dropZone.querySelector('.drop-zone-content').innerHTML =
      `<p><strong>${file.name}</strong> (${currentImage.width} &times; ${currentImage.height})</p>
       <p class="hint">Click to change</p>`;
  } catch (err) {
    alert('Could not load image. Please try a different file.');
  }
}

// --- Process ---

processBtn.addEventListener('click', async () => {
  if (!currentImage) return;

  processBtn.disabled = true;
  progressSection.classList.remove('hidden');
  resultsSection.classList.add('hidden');

  try {
    const style = styleSelect.value;
    const result = await process(currentImage, style, (fraction, text) => {
      progressBar.style.width = `${Math.round(fraction * 100)}%`;
      progressText.textContent = text;
    });

    // Display results
    drawImageToCanvas(originalCanvas, currentImage);
    drawGrayscaleToCanvas(resultCanvas, result.data, result.width, result.height);

    progressSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
  } catch (err) {
    console.error('Processing failed:', err);
    progressText.textContent = `Error: ${err.message}`;
    progressBar.style.width = '0%';
  } finally {
    processBtn.disabled = false;
  }
});

// --- Downloads ---

downloadJpg.addEventListener('click', () => {
  downloadCanvas(resultCanvas, 'crosshatch.jpg', 'image/jpeg', 0.92);
});

downloadPng.addEventListener('click', () => {
  downloadCanvas(resultCanvas, 'crosshatch.png', 'image/png');
});

// --- Try another ---

tryAnother.addEventListener('click', () => {
  currentImage = null;
  fileInput.value = '';
  controls.classList.add('hidden');
  resultsSection.classList.add('hidden');
  progressSection.classList.add('hidden');
  progressBar.style.width = '0%';

  dropZone.querySelector('.drop-zone-content').innerHTML = dropZoneInitialHTML;
});
