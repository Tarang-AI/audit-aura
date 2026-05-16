import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            // Silently handle common proxy errors during backend restarts or high load
            const errorMessage = err.message || '';
            const errorCode = (err as any).code || '';
            
            const isSocketError = 
              errorMessage.includes('EPIPE') || 
              errorMessage.includes('ECONNRESET') || 
              errorMessage.includes('ended by the other party') ||
              errorCode === 'EPIPE' ||
              errorCode === 'ECONNRESET';

            if (isSocketError) {
              return;
            }
            console.error('proxy error', err);
          });
        },
      },
      // Proxy backend endpoints directly
      '/controls': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/upload': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/upload-url': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ingest': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/pdfs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/dashboard': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/compliance-score': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/violations': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});

// Made with Bob
