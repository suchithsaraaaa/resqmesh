import 'react-native-get-random-values';
import {AppRegistry} from 'react-native';

// Polyfill safeguard for Hermes release bundle
if (typeof global.crypto === 'undefined') {
  global.crypto = {};
}
if (typeof global.crypto.getRandomValues !== 'function') {
  global.crypto.getRandomValues = function (array) {
    for (var i = 0; i < array.length; i++) {
      array[i] = Math.floor(Math.random() * 256);
    }
    return array;
  };
}

import App from './App';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => App);
