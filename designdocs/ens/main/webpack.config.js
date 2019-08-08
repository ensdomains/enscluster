var path = require('path');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'views/lib'),
    filename: 'eventutils.js',
    libraryTarget: 'commonjs2'
  },
  mode: 'production'
};
