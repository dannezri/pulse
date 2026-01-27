import * as React from 'react';

import { PulseHealthkitViewProps } from './PulseHealthkit.types';

export default function PulseHealthkitView(props: PulseHealthkitViewProps) {
  return (
    <div>
      <iframe
        style={{ flex: 1 }}
        src={props.url}
        onLoad={() => props.onLoad({ nativeEvent: { url: props.url } })}
      />
    </div>
  );
}
