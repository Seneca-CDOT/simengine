
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import socket from '../../../images/socket.svg';
import Led from './Led';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * Outlet Graphics
 */
class Socket extends React.Component {

    constructor(props) {
      super();
      this.state = {
        // coordinates
        x: props.x,
        y: props.y,
        // graphics
        assetImage: null,
        bgImage: null,
      };

      // Socket may have background image (static asset)
      if (props.asset && 'imgUrl' in props.asset) {
        const bgImage = new window.Image();
        bgImage.src = props.asset.imgUrl;
        bgImage.onload = () => {
          
          // resize the background image 
          const oldHeight = bgImage.height;
          bgImage.height = 160;
          bgImage.width = bgImage.width / (oldHeight/160);

          this.setState({ bgImage });
        };
      }
    }


    /** Load Socket Image */
    componentDidMount() {
      const assetImage = new window.Image();
      assetImage.src = socket;
      assetImage.onload = () => { this.setState({ assetImage }); };
    }


    /** Notify Parent of Selection */
    handleClick = () => {
      this.props.onElementSelection(this.props.assetId, this.props.asset);
    };

    /** Notify Parent of Asset Transformation */
    updateSocketPos = (s) => {
      this.refs.assetGroup.setZIndex(100); 

      const coord = {
        x: s.target.attrs.x, // asset position - x
        y: s.target.attrs.y, // asset position - y
        inputConnections: [
          {
            x: this.state.assetImage.width * 0.5,  // power input location - x
            y: this.state.assetImage.height * 0.5, // power input location - y
          }
        ],
      };

      this.setState(coord);
      this.props.onPosChange(this.props.assetId, coord);
    }

    render() {

      const { bgImage, assetImage, x, y } = this.state;

      // Selected when either parent element (e.g. PDU outlet belongs to) is selected
      // or the socket was selected
      const strokeColor = (this.props.selected || this.props.parentSelected) ? colors.selectedAsset: colors.deselectedAsset;

      return(
        <Group
          x={x}
          y={y}
          draggable={this.props.draggable}
          onDragMove={this.updateSocketPos.bind(this)}
          onClick={this.handleClick}
          ref="assetGroup"
        >

          {/* Optional background image */}
          {bgImage &&
            <Image
              image={bgImage}
              stroke={strokeColor}
              strokeWidth={4}
            />
          }

          {/* Outlet Image */}
          <Image
            image={assetImage}
            stroke={strokeColor}            
          />

          {/* LED */}
          <Led socketOn={this.props.asset.status} powered={this.props.powered}/>
          
          {/* Socket title */}
          {!this.props.hideName &&
            <Text 
              fontSize={this.props.fontSize} 
              fontFamily={'Helvetica'} 
              text={(this.props.asset && this.props.asset.name) ? this.props.asset.name : 'socket'}  
              y={((bgImage) ? (bgImage.height) : (assetImage?(assetImage.height):0)) + 30} 
            />
          }

        </Group>
      );
    }
}

Socket.socketSize = () => {
  return new Promise((resolve, reject) => {
    let img = new window.Image();
    img.src = socket;
    img.onload = () => resolve({ height: img.height, width: img.width });
    img.onerror = reject;
  });
};

Socket.defaultProps = {
  fontSize: 14,
  draggable: false
};

Socket.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  onPosChange: PropTypes.func.isRequired, // called on asset position change
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
  draggable: PropTypes.bool, // Indicates if the outlet can be dragged
  asset: PropTypes.object, // Asset Details
  assetId: PropTypes.string, // Asset Key
  selected: PropTypes.bool, // Selected by user
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  onElementSelection: PropTypes.func, // Notify parent component of selection
  hideName: PropTypes.bool, // Display outlet name
  fontSize: PropTypes.number, // Asset name font
};

export default Socket;