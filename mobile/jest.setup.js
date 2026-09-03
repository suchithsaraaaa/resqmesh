/* eslint-disable no-undef */

jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  const inset = { top: 0, right: 0, bottom: 0, left: 0 };
  const frame = { x: 0, y: 0, width: 390, height: 844 };
  const SafeAreaInsetsContext = React.createContext(inset);
  const SafeAreaFrameContext = React.createContext(frame);

  return {
    SafeAreaProvider: ({ children }) => children,
    SafeAreaConsumer: ({ children }) => children(inset),
    SafeAreaInsetsContext,
    SafeAreaFrameContext,
    useSafeAreaInsets: () => inset,
    useSafeAreaFrame: () => frame,
  };
});

jest.mock('react-native-screens', () => {
  const React = require('react');
  const RN = require('react-native');
  return {
    enableScreens: jest.fn(),
    ScreenContainer: ({ children }) => React.createElement(RN.View, null, children),
    Screen: ({ children }) => React.createElement(RN.View, null, children),
    NativeScreen: ({ children }) => React.createElement(RN.View, null, children),
    NativeScreenContainer: ({ children }) => React.createElement(RN.View, null, children),
    ScreenStack: ({ children }) => React.createElement(RN.View, null, children),
    ScreenStackHeaderConfig: () => null,
    ScreenStackHeaderRightView: () => null,
    ScreenStackHeaderLeftView: () => null,
    ScreenStackHeaderTitleView: () => null,
    ScreenStackHeaderCenterView: () => null,
    ScreenStackHeaderSearchBarView: () => null,
    SearchBar: () => null,
  };
});

jest.mock('react-native-sqlite-storage', () => ({
  DEBUG: jest.fn(),
  enablePromise: jest.fn(),
  openDatabase: jest.fn(() =>
    Promise.resolve({
      executeSql: jest.fn(() => Promise.resolve([[], { rows: { length: 0, item: () => ({}) } }])),
      transaction: jest.fn((tx) => tx({ executeSql: jest.fn() })),
    })
  ),
}));
