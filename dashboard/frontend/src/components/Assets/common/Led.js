import React from 'react';
import { Rect } from 'react-konva';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * LED (green if asset is 'on', red if 'off', grey if not powered)
 */
const Led = ({ powered, socketOn, x, y }) => {
  const color = powered
    ? socketOn
      ? colors.ledStatusOn
      : colors.red
    : colors.ledStatusOff;
  return (
    <Rect x={x} y={y} width={10} height={10} fill={color} shadowBlur={3} />
  );
};

Led.defaultProps = {
  y: 85,
  x: 20,
};

Led.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  socketOn: PropTypes.number.isRequired, // socket status
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
};

export default Led;
