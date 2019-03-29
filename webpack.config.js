const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const ManifestPlugin = require('webpack-manifest-plugin');
const TSLintPlugin = require('tslint-webpack-plugin');

/*
 * SplitChunksPlugin is enabled by default and replaced
 * deprecated CommonsChunkPlugin. It automatically identifies modules which
 * should be splitted of chunk by heuristics using module duplication count and
 * module category (i. e. node_modules). And splits the chunks…
 *
 * It is safe to remove "splitChunks" from the generated configuration
 * and was added as an educational example.
 *
 * https://webpack.js.org/plugins/split-chunks-plugin/
 *
 */

/*
 * We've enabled UglifyJSPlugin for you! This minifies your app
 * in order to load faster and run less javascript.
 *
 * https://github.com/webpack-contrib/uglifyjs-webpack-plugin
 *
 */

const devMode = process.env.NODE_ENV !== 'production'


module.exports = {
  entry: {
    scripts: './animeu/static/scripts/index.ts',
    styles: './animeu/static/styles/index.css'
  },
  output: {
    filename: devMode ? '[name].js' : '[name].[chunkhash].js',
    path: path.resolve(__dirname, 'build'),
  },
  resolve: {
    extensions: ['.js', '.ts', '.css']
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: devMode ? '[name].css' : '[name].[hash].css',
      chunkFilename: devMode ? '[id].css' : '[id].[hash].css',
    }),
    new ManifestPlugin({
      writeToFileEmit: true,
      generate: (seed, files) => files.reduce(
        ({ assets, ...other }, { name, path }) => ({
          ...other,
          'assets': { ...assets, [name]: path }
        }),
        seed
      )
    }),
    new TSLintPlugin({
      files: ['./animeu/static/**/*.ts'],
      waitForLinting: devMode ? false : true,
      warningsAsError: devMode ? false : true,
    })
  ],
  devtool: 'inline-source-map',
  devServer: {
    contentBase: path.join(__dirname, 'build'),
    compress: true,
    port: 9000
  },
	module: {
		rules: [
			{
        test: /\.[tj]s$/,
        exclude: /node_modules/,
				use: 'ts-loader'
      },
			{
        test: /\.css$/,
        exclude: /node_modules/,
        use: [
          'style-loader',
          MiniCssExtractPlugin.loader,
          'css-loader',
          'postcss-loader'
        ]
			}
		]
	},
	mode: devMode ? 'development' : 'production'
};
