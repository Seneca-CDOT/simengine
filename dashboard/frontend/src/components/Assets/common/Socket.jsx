import React from 'react';
import PropTypes from 'prop-types';
import { Text, Image, Group } from 'react-konva';

// ** components
import Led from './Led';
import Asset from './Asset';

// ** misc
import socketSource from '../../../images/socket.png';
import colors from '../../../styles/colors';
import PointerElement from './PointerElement';

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
    const backgroundImg =
      'imgUrl' in this.props.asset ? this.props.asset['imgUrl'] : null;

    Promise.all(
      this.loadImages({ socketImg: socketSource, backgroundImg }),
    ).then(() => {
      let { backgroundImg } = this.state;
      if (backgroundImg) {
        // resize the image
        backgroundImg.width =
          backgroundImg.width / (backgroundImg.height / 160);
        backgroundImg.height = 160;
        this.setState({ backgroundImg });
      }

      this.props.onPosChange(
        this.props.asset.key,
        this.formatAssetCoordinates(this.props),
      );
    });
  }

  getInputCoordinates = (center = true) => [
    center && this.state.socketImg
      ? {
          x: this.state.socketImg.width * 0.5,
          y: this.state.socketImg.height * 0.5,
        }
      : { x: 0, y: 0 },
  ];

  render() {
    const { backgroundImg, socketImg } = this.state;

    // Selected when either parent element (e.g. PDU outlet belongs to) is selected
    // or the socket was selected
    const strokeColor =
      this.props.selected || this.props.parentSelected
        ? colors.selectedAsset
        : colors.deselectedAsset;

    return (
      <PointerElement>
        <Group
          x={this.props.x}
          y={this.props.y}
          ref="asset"
          draggable={!this.props.isComponent}
          onDragMove={this.updateAssetPos.bind(this)}
          onClick={this.handleClick}
        >
          {/* Optional background image */}
          {backgroundImg && (
            <Image image={backgroundImg} stroke={strokeColor} strokeWidth={4} />
          )}

          {/* Outlet Image */}
          <Image image={socketImg} stroke={strokeColor} strokeWidth={4} />

          {/* LED */}
          <Led
            socketOn={this.props.asset.status}
            powered={this.props.powered}
          />

          {/* Socket title */}
          {!this.props.hideName && (
            <Text
              fontSize={this.props.fontSize}
              fontFamily={'Helvetica'}
              text={
                this.props.asset && this.props.asset.name
                  ? this.props.asset.name
                  : 'socket'
              }
              y={
                (backgroundImg
                  ? backgroundImg.height
                  : socketImg
                  ? socketImg.height
                  : 0) + 30
              }
            />
          )}
        </Group>
      </PointerElement>
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

Socket.defaultProps = { fontSize: 14, isComponent: false };

Socket.propTypes = {
  isComponent: PropTypes.bool, // Indicates if the outlet can be dragged
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  hideName: PropTypes.bool,
};

export default Socket;
