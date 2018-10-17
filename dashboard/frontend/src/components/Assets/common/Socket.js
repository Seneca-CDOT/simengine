
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
        assetImg: null,
        backgroundImg: null,
      };

      // Socket may have a background image (static asset)
      if (props.asset && 'imgUrl' in props.asset) {
        const backgroundImg = new window.Image();
        backgroundImg.src = props.asset.imgUrl;
        backgroundImg.onload = () => {
          
          // resize the background image 
          const oldHeight = backgroundImg.height;
          backgroundImg.height = 160;
          backgroundImg.width = backgroundImg.width / (oldHeight/160);

          this.setState({ backgroundImg });
        };
      }
    }


    /** Load Socket Image */
    componentDidMount() {
      const assetImg = new window.Image();
      assetImg.src = socket;
      assetImg.onload = () => { this.setState({ assetImg }); };
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
            x: this.state.assetImg.width * 0.5,  // power input location - x
            y: this.state.assetImg.height * 0.5, // power input location - y
          }
        ],
      };

      this.setState(coord);
      this.props.onPosChange(this.props.assetId, coord);
    }

    render() {

      const { backgroundImg, assetImg, x, y } = this.state;

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
          {backgroundImg &&
            <Image
              image={backgroundImg}
              stroke={strokeColor}
              strokeWidth={4}
            />
          }

          {/* Outlet Image */}
          <Image
            image={assetImg}
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
              y={((backgroundImg) ? (backgroundImg.height) : (assetImg?(assetImg.height):0)) + 30} 
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