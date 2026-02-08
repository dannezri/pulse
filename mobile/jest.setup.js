// Jest setup file - Minimal mocks

// Mock lucide-react-native icons
jest.mock('lucide-react-native', () => ({
  TrendingDown: 'TrendingDown',
  Clock: 'Clock',
  AlertTriangle: 'AlertTriangle',
  Calendar: 'Calendar',
  CheckCircle: 'CheckCircle',
  ChevronDown: 'ChevronDown',
  ChevronUp: 'ChevronUp',
  Zap: 'Zap',
}));
