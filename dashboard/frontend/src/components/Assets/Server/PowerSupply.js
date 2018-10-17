
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import psuimg from '../../../images/power-supply.svg';
import Led from '../common/Led';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * Power Supply Graphics
 */
export default class PowerSupply extends React.Component {

    constructor() {
      super();
      this.state = {
        assetImage: null,
      };
    }


    /** Load Socket Image */
    componentDidMount() {
      const assetImage = new window.Image();
      assetImage.src = psuimg;
      assetImage.onload = () => { this.setState({assetImage}); };
    }

     /** Notify Parent of Selection */
    handleClick = () => {
      this.props.onElementSelection(this.props.assetId, this.props.asset);
    };

    render() {
      const strokeColor = (this.props.selected || this.props.parentSelected) ? colors.selectedAsset : colors.deselectedAsset;
      
      return(
        <Group
          x={this.props.x}
          y={this.props.y}
        >
          {/*PSU graphics */}
          <Image
            image={this.state.assetImage}
            stroke={strokeColor}
            strokeWidth={4}
            onClick={this.handleClick}
          />

          {/* LED & label*/}
          <Led socketOn={this.props.asset.status} powered={this.props.powered} />
          <Text text={this.props.asset && this.props.asset.name ? this.props.asset.name :'psu'}  y={105} />
        </Group>
      );
    }
}

PowerSupply.socketSize = () => {
  return new Promise((resolve, reject) => {
    let img = new window.Image();
    img.src = psuimg;
    img.onload = () => resolve({ height: img.height, width: img.width });
    img.onerror = reject;
  });
};


PowerSupply.defaultProps = {
  y: 0,
};

PowerSupply.propTypes = {
  x: PropTypes.number,
  y: PropTypes.number, 

  asset: PropTypes.object, // Asset Details
  assetId: PropTypes.string, // Asset Key

  selected: PropTypes.bool, // Selected by user
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
  parentSelected: PropTypes.bool, // Is parent asset selected?
  onElementSelection: PropTypes.func, // Notify parent component of selection
};
