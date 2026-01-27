import { registerWebModule, NativeModule } from 'expo';

import { PulseHealthkitModuleEvents } from './PulseHealthkit.types';

class PulseHealthkitModule extends NativeModule<PulseHealthkitModuleEvents> {
  PI = Math.PI;
  async setValueAsync(value: string): Promise<void> {
    this.emit('onChange', { value });
  }
  hello() {
    return 'Hello world! 👋';
  }
}

export default registerWebModule(PulseHealthkitModule, 'PulseHealthkitModule');
