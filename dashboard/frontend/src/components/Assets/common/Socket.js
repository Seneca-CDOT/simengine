
import React from 'react';
import PropTypes from 'prop-types';
import { Text, Image, Group } from 'react-konva';

// ** components
import Led from './Led';
import Asset from './Asset';

// ** misc
import socketSource from '../../../images/socket.svg';
import colors from '../../../styles/colors';


/**
 * Outlet Graphics
 */
class Socket extends Asset {

    constructor(props) {
      super(props);
      this.state = {
        // graphics
        socketImg: null,
        backgroundImg: null,
      };
    }

    /** Load Socket Image */
    componentDidMount() {
      const backgroundImg = 'imgUrl' in this.props.asset?this.props.asset['imgUrl']:null;

      Promise.all(this.loadImages({ socketImg: socketSource, backgroundImg })).then(() => {
        let { backgroundImg } = this.state;
        if (backgroundImg) {
          // resize the image
          backgroundImg.width = backgroundImg.width / (backgroundImg.height/160);
          backgroundImg.height = 160;
          this.setState({ backgroundImg });
        }
      });
    }
    
    getInputCoordinates = (center=true) => [{ x: (center?this.state.socketImg.width*0.5:0), y: (center?this.state.socketImg.height*0.5:0), }];

    render() {

      const { backgroundImg, socketImg, x, y } = this.state;

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
          <Image image={socketImg} stroke={strokeColor}            />

          {/* LED */}
          <Led socketOn={this.props.asset.status} powered={this.props.powered}/>
          
          {/* Socket title */}
          {!this.props.hideName &&
            <Text 
              fontSize={this.props.fontSize} 
              fontFamily={'Helvetica'} 
              text={(this.props.asset && this.props.asset.name) ? this.props.asset.name : 'socket'}  
              y={((backgroundImg) ? (backgroundImg.height) : (socketImg?(socketImg.height):0)) + 30} 
            />
          }

        </Group>
      );
    }
}

Socket.socketSize = () => {
  return new Promise((resolve, reject) => {
    let img = new window.Image();
    img.src = socketSource;
    img.onload = () => resolve({ height: img.height, width: img.width });
    img.onerror = reject;
  });
};

Socket.defaultProps = { fontSize: 14, draggable: false };

Socket.propTypes = {
  draggable: PropTypes.bool, // Indicates if the outlet can be dragged
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  hideName: PropTypes.bool, // Display outlet name
  fontSize: PropTypes.number, // Asset name font
};

export default Socket;