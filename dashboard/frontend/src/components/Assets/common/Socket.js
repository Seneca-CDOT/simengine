
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import socket from '../../../images/socket.svg';
import Led from './Led';
import PropTypes from 'prop-types';

import Asset from './Asset';
import colors from '../../../styles/colors';


/**
 * Outlet Graphics
 */
class Socket extends Asset {

    constructor(props) {
      super(props);
      this.state = {

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
    
    getInputCoordinates = (center=true) => [{ x: (center?this.state.assetImg.width*0.5:0), y: (center?this.state.assetImg.height*0.5:0), }];

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
          onDragMove={this.updateAssetPos.bind(this)}
          onClick={this.handleClick}
          ref="asset"
        >

          {/* Optional background image */}
          {backgroundImg && <Image image={backgroundImg} stroke={strokeColor} strokeWidth={4}/>}

          {/* Outlet Image */}
          <Image image={assetImg} stroke={strokeColor}            />

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
  draggable: PropTypes.bool, // Indicates if the outlet can be dragged
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  hideName: PropTypes.bool, // Display outlet name
  fontSize: PropTypes.number, // Asset name font
};

export default Socket;