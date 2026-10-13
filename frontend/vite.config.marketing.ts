import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'
import { renameSync, existsSync } from 'fs'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    react(),
    {
      // GitHub Pages requires index.html; rename from the input-derived filename.
      name: 'rename-marketing-html',
      closeBundle() {
        const src = resolve(__dirname, 'dist-marketing', 'index.marketing.html')
        const dst = resolve(__dirname, 'dist-marketing', 'index.html')
        if (existsSync(src)) renameSync(src, dst)
      },
    },
  ],
  base: '/SpotWeldPro-AI/',
  build: {
    outDir: 'dist-marketing',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'index.marketing.html'),
    },
  },
})
