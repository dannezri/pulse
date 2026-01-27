import { requireNativeView } from 'expo';
import * as React from 'react';

import { PulseHealthkitViewProps } from './PulseHealthkit.types';

const NativeView: React.ComponentType<PulseHealthkitViewProps> =
  requireNativeView('PulseHealthkit');

export default function PulseHealthkitView(props: PulseHealthkitViewProps) {
  return <NativeView {...props} />;
}
