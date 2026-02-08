const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const config = getDefaultConfig(__dirname);

// Add babel-plugin-module-resolver alias support
config.resolver.alias = {
  '@': path.resolve(__dirname, 'src'),
};

module.exports = config;
