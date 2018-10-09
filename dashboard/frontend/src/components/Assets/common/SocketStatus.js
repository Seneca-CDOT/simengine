import React from 'react';
import { Rect } from 'react-konva';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * LED of a socket
 */
function SocketStatus({ powered, socketOn, x, y }) {
    const color = powered?(socketOn?"green": colors.red):"grey";
    return (
      <Rect
        x={x}
        y={y}
        width={10}
        height={10}
        fill={color}
        shadowBlur={5}
       />
    );
}


SocketStatus.defaultProps = {
  red_means_on: false,
  y: 85,
  x: 20
};

SocketStatus.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  socketOn: PropTypes.number.isRequired, // socket status
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present

};

export default SocketStatus;
