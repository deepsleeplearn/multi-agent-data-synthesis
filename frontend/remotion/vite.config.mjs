import react from '@vitejs/plugin-react';
import {fileURLToPath} from 'node:url';
import {defineConfig} from 'vite';

const remotionRoot = fileURLToPath(new URL('.', import.meta.url));
const entry = fileURLToPath(new URL('./src/main.jsx', import.meta.url));
const outDir = fileURLToPath(new URL('../static', import.meta.url));

export default defineConfig({
  root: remotionRoot,
  plugins: [react()],
  build: {
    outDir,
    emptyOutDir: false,
    sourcemap: false,
    rollupOptions: {
      input: entry,
      output: {
        entryFileNames: 'remotion-login.js',
        inlineDynamicImports: true,
      },
    },
  },
});
