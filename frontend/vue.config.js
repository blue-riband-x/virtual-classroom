const { defineConfig } = require('@vue/cli-service')
const http = require('http')
// 增大全局 HTTP 头大小限制，解决 431 Request Header Fields Too Large
http.globalAgent.maxHeaderSize = 65536

module.exports = defineConfig({
  transpileDependencies: false,

  devServer: {
    port: 8080,
    historyApiFallback: true,
    proxy: {
      // Java Spring Boot (8081) — 传统CRUD
      '/api/v1/auth': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true
      },
      '/api/v1/users': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true
      },
      '/api/v1/leaderboard': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true
      },
      // 大纲 AI 生成 → Python (8000)
      // 注意：必须在通用 /api/v1/outline 规则之前
      '/api/v1/outline/generate': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api/v1/outline/pdf-generate': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api/v1/outline/stream': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      // 大纲 CRUD → Java (8081)
      '/api/v1/outline': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true
      },
      // AI 业务 → Python (8000)
      '/api/v1/ai': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        onProxyRes: (proxyRes, req, res) => {
          if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
            res.setHeader('Cache-Control', 'no-cache, no-transform')
            res.setHeader('X-Accel-Buffering', 'no')
            delete proxyRes.headers['content-length']
          }
        }
      },
      // 板书图片等静态资源 → Python (8000)
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
