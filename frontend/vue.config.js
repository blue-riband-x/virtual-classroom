const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: false,

  // ========== API代理配置（连接FastAPI后端）==========
  devServer: {
    port: 8080,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // ====== SSE 支持：禁用代理响应缓冲 ======
        onProxyRes: (proxyRes, req, res) => {
          // 对 SSE 流禁用压缩和缓冲
          if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
            res.setHeader('Cache-Control', 'no-cache, no-transform')
            res.setHeader('X-Accel-Buffering', 'no')
            // 禁用压缩以确保实时传输
            delete proxyRes.headers['content-length']
          }
        }
      }
    }
  }
})
