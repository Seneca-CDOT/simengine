import React from 'react';
import { Rect, Group, Text } from 'react-konva';
import PropTypes from 'prop-types';

// ** misc
import colors from '../../../styles/colors';

/**
 * Load LED display
 */
const LEDDisplay = ({ load, x, y, status }) => (
  <Group x={x} y={y}>
    <Rect
      width={60}
      height={60}
      fill={colors.ledBackground}
      stroke={colors.ledStroke}
    />
    <Text
      y={10}
      x={5}
      text={load > 9 ? '' + load : '0' + load}
      fontFamily={'DSEG7Modern'}
      fontSize={30}
      fill={status ? colors.ledText : colors.ledStatusOff}
    />
    <Text y={65} x={8} text={'AMPS'} />
  </Group>
);

LEDDisplay.propTypes = {
  x: PropTypes.number.isRequired, // X position of the asset
  y: PropTypes.number.isRequired, // Y position of the asset
  load: PropTypes.number.isRequired, // load value
  status: PropTypes.bool.isRequired, // on/off
};

export default LEDDisplay;
