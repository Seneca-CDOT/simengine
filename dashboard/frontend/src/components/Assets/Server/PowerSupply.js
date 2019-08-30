import React from 'react';
import PropTypes from 'prop-types';
import { Text, Image, Group } from 'react-konva';

// ** components
import Asset from '../common/Asset';
import Led from '../common/Led';
import PointerElement from '../common/PointerElement';

// ** misc
import psuSource from '../../../images/power-supply.svg';
import colors from '../../../styles/colors';

/**
 * Power Supply Graphics
 */
export default class PowerSupply extends Asset {
  constructor(props) {
    super(props);
    this.state = { psuImg: null };
  }

  /** Load Socket Image */
  componentDidMount() {
    this.loadImages({ psuImg: psuSource });
  }

  render() {
    const strokeColor =
      this.props.selected || this.props.parentSelected
        ? colors.selectedAsset
        : colors.deselectedAsset;
    const { psuImg } = this.state;

    return (
      <PointerElement>
        <Group x={this.props.x} y={this.props.y} ref="asset">
          {/* PSU graphics */}
          <Image
            image={psuImg}
            stroke={strokeColor}
            strokeWidth={4}
            onClick={this.handleClick}
          />

          {/* LED & label*/}
          <Led
            socketOn={this.props.asset.status}
            powered={this.props.powered}
          />
          <Text text={this.props.asset.name} y={104} fontSize={14} />
        </Group>
      </PointerElement>
    );
  }
}

PowerSupply.psuSize = () => {
  return new Promise((resolve, reject) => {
    let img = new window.Image();
    img.src = psuSource;
    img.onload = () => resolve({ height: img.height, width: img.width });
    img.onerror = reject;
  });
};

PowerSupply.propTypes = {
  parentSelected: PropTypes.bool, // Is parent asset selected?
};
