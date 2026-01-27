# Expo + React Native Project Rules (STRICT)

This project uses:
- Expo SDK 54 (managed workflow)
- React 19.1.0
- React Native 0.81.5
- Expo Router 6

General rules:
1. Never change versions of expo, react, or react-native unless explicitly requested.
2. Never install React Native or Expo-related libraries with "npm install".
   Always use: npx expo install <package>.
3. Before suggesting any new dependency, verify that it is compatible with Expo managed workflow.
4. If a library requires native code changes, pods, gradle, or prebuild, clearly warn and propose an Expo-compatible alternative.
5. After any dependency change, always run: npx expo-doctor and fix all issues before continuing.
6. Do not suggest random or unverified libraries.

Documentation policy:
- Before suggesting or modifying dependencies, read:
  - docs/stack.md
  - docs/deps-policy.md

Goal:
Prevent version mismatches, incompatible native modules, and unstable installs.
