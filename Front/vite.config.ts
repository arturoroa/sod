import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

function frontTracePlugin(): Plugin {
  return {
    name: 'front-trace-terminal',
    configureServer(server) {
      server.middlewares.use('/__front_trace', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 404;
          res.end();
          return;
        }

        const chunks: Buffer[] = [];
        req.on('data', (chunk) => {
          chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
        });

        req.on('end', () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf8') || '{}';
            const data = JSON.parse(raw);
            const now = new Date().toISOString();
            const traceId = data?.traceId ?? 'no-trace-id';
            const step = data?.step ?? 'NO_STEP';
            if (data?.payload !== undefined) {
              console.log(`[FRONT-TRACE][${now}][${traceId}] ${step}`, data.payload);
            } else {
              console.log(`[FRONT-TRACE][${now}][${traceId}] ${step}`);
            }
          } catch (error) {
            console.log('[FRONT-TRACE] Failed to parse trace payload', error);
          }

          res.statusCode = 204;
          res.end();
        });

        req.on('error', () => {
          res.statusCode = 500;
          res.end();
        });
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), frontTracePlugin()],
  resolve: {
    alias: {
      'react-native': path.resolve(__dirname, 'src/shims/react-native.tsx'),
      'react-native-webview': path.resolve(__dirname, 'src/shims/react-native-webview.tsx'),
      'expo-document-picker': path.resolve(__dirname, 'src/shims/expo-document-picker.ts'),
      '@react-native-picker/picker': path.resolve(__dirname, 'src/shims/react-native-picker.tsx'),
      'lucide-react-native': path.resolve(__dirname, 'src/shims/lucide-react-native.tsx'),
    },
  },
  server: {
    port: 8081,
  },
});
