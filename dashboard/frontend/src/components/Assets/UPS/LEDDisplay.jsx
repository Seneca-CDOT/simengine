import React from 'react';
import { Image, Group, Text } from 'react-konva';
import PropTypes from 'prop-types';

// ** misc
import colors from '../../../styles/colors';

/**
 * Load LED display
 */
const LEDDisplay = ({ battery, x, y, status, upsMonitorImg }) => {
  const fontFamily = 'DSEG14Modern';
  const fontSize = 16;

  const fill = status ? colors.ledTextWhite : colors.ledStatusOff;
  let chargeBar = '|'.repeat(35 * (battery * 0.001));

  return (
    <Group x={x} y={y}>
      <Image image={upsMonitorImg} />
      <Group y={50} x={18}>
        <Text
          text={`Output ${status ? 'ON' : 'OFF'}`}
          fontFamily={fontFamily}
          fontSize={fontSize}
          fill={fill}
        />
        <Text
          y={30}
          text={`Batt ${Math.floor(battery / 10)}%`}
          fontFamily={fontFamily}
          fontSize={fontSize}
          fill={fill}
        />
        <Text y={30} x={110} text={chargeBar} fontSize={fontSize} fill={fill} />
      </Group>
    </Group>
  );
};

LEDDisplay.propTypes = {
  x: PropTypes.number.isRequired, // X position of the asset
  y: PropTypes.number.isRequired, // Y position of the asset
  battery: PropTypes.number.isRequired, // battery level
  status: PropTypes.bool.isRequired, // on/off
  upsMonitorImg: PropTypes.object, // background image
};

export default LEDDisplay;
