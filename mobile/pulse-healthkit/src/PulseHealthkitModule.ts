import { NativeModule, requireNativeModule } from 'expo';

import { PulseHealthkitModuleEvents } from './PulseHealthkit.types';

declare class PulseHealthkitModule extends NativeModule<PulseHealthkitModuleEvents> {
  PI: number;
  hello(): string;
  setValueAsync(value: string): Promise<void>;
}

// This call loads the native module object from the JSI.
export default requireNativeModule<PulseHealthkitModule>('PulseHealthkit');
