const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: false,

  devServer: {
    port: 8080,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 默认：Python AI 后端
        changeOrigin: true,
        router: function(req) {
          const path = req.url || req.path
          // 传统 CRUD 业务 → Java Spring Boot (8081)
          if (path.startsWith('/api/auth') ||
              path.startsWith('/api/users') ||
              path.startsWith('/api/leaderboard') ||
              (path.startsWith('/api/outline') &&
               (path === '/api/outline/my' || /^\/api\/outline\/\d+/.test(path)))) {
            return 'http://127.0.0.1:8081'
          }
          // AI 业务 → Python FastAPI (8000)
          return 'http://127.0.0.1:8000'
        },
        onProxyRes: (proxyRes, req, res) => {
          if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
            res.setHeader('Cache-Control', 'no-cache, no-transform')
            res.setHeader('X-Accel-Buffering', 'no')
            delete proxyRes.headers['content-length']
          }
        }
      }
    }
  }
})
