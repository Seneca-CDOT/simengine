/* eslint-disable */

import React from 'react';
import ReactDOM from 'react-dom';
import MuiThemeProvider from '@material-ui/core/styles/MuiThemeProvider';

// COMPONENTS
import App from './components/App';

// STYLES
import 'normalize.css';
import './styles/app.scss';
import theme from './styles/theme';

ReactDOM.render(
  <MuiThemeProvider theme={theme}>
    <App />
  </MuiThemeProvider>,
  document.getElementById('app'),
);
