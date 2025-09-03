const { defineConfig } = require('@vue/cli-service')
const CompressionPlugin = require("compression-webpack-plugin")

module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    plugins: [
      new CompressionPlugin({
        test: /\.js$|\.html$|\.css$|\.jpe?g$|\.png$|\.svg$|\.webp$|gif$|\.xlsx$|\.ttf$|\.woff$|\.woff2/,
        threshold: 10 * 1024,
        deleteOriginalAssets: false,
      }),
    ],
  },
})
