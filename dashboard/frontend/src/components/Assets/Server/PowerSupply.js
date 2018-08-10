
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import psimg from '../../../images/power-supply.svg';
import SocketStatus from '../common/SocketStatus';
import PropTypes from 'prop-types';


/**
 * Outlet Graphics
 */
export default class PowerSupply extends React.Component {

    constructor(props) {
      super();
      this.state = {
        image: null,
        color: 'grey',
        x: props.x?props.x:40,
        y:0,
      };
    }


    /** Load Socket Image */
    componentDidMount() {
      const image = new window.Image();
      image.src = psimg;
      image.onload = () => {
        // setState will redraw layer
        // because "image" property is changed
        this.setState({
          image: image
        });
      };

    }

     /** Notify Parent of Selection */
    handleClick = () => {
      if (this.props.selectable) {
        this.props.onElementSelection(this.props.assetId, this.props.asset);
      }
    };

    updateSocketPos = (s) => {
      this.setState({ x: s.target.attrs.x, y : s.target.attrs.y });
      this.props.onPosChange(this.props.assetId, s);
    }

    render() {

      let strokeColor = this.state.color;

      // Selected when either parent element (e.g. PDU outlet belongs to) is selected
      // or the socket was selected
      if (this.props.selectable) {
        strokeColor = (this.props.selected || this.props.parentSelected) ? "blue" : "grey";
      }

      return(
        <Group
          x={this.state.x}
          y={this.state.y}
          onDragMove={this.updateSocketPos.bind(this)}
        >
          <Image
            image={this.state.image}
            stroke={strokeColor}
            onClick={this.handleClick}
          />

          {/* LED */}
          {this.props.selectable &&
            <SocketStatus socketOn={this.props.red_means_on?!this.props.asset.status:this.props.asset.status} powered={this.props.powered}/>
          }
          <Text text={this.props.asset && this.props.asset.name ? this.props.asset.name :'socket'}  y={this.state.bgImage ? 175: 105} />
        </Group>
      );
    }
}

PowerSupply.defaultProps = {
  red_means_on: false,
};

PowerSupply.propTypes = {
  x: PropTypes.number,
  onPosChange: PropTypes.func, // called on asset position change
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
  asset: PropTypes.object, // Asset Details
  assetId: PropTypes.string, // Asset Key
  selected: PropTypes.bool, // Selected by user
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  onElementSelection: PropTypes.func, // Notify parent component of selection
  selectable: PropTypes.bool.isRequired, // Outlet is an asset
  red_means_on: PropTypes.bool,
};
