import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    // three.js 자체가 크기 때문에(약 500KB) 경고가 뜨는데, 프로토타입에서는 문제가 아니라서 기준을 올려 경고를 끈다
    chunkSizeWarningLimit: 800,
  },
});
