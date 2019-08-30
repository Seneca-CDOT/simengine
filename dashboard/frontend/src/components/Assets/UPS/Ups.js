import React from 'react';
import { Text, Group, Image } from 'react-konva';

import upsMonitorSource from '../../../images/ups_monitor_2.png';
import c14Source from '../../../images/c14.svg';
import Socket from '../common/Socket';

import OutputAsset from '../common/OutputAsset';
import AssetOutline from '../common/AssetOutline';
import LEDDisplay from './LEDDisplay';

import paths from '../../../styles/paths';

/**
 * Draw Ups graphics
 */
export default class Ups extends OutputAsset {
  constructor(props) {
    super(props);
    this.state = {
      socketSize: { width: 0, height: 0 },
      upsMonitorImg: null,
      c14Img: null,
    };

    this.inputSocketPos = { x: 254, y: 5 };

    // set outlet properties (spacing between rows/cols etc..)
    this.outputSpacing = { x: 20, y: 30 };
    this.outputStartPosition = { x: 250, y: 120 };
  }

  componentDidMount() {
    Promise.all(
      this.loadImages({ upsMonitorImg: upsMonitorSource, c14Img: c14Source }),
    )
      .then(Socket.socketSize)
      .then(size => {
        this.setState({ socketSize: size });
      })
      .then(() =>
        this.props.onPosChange(
          this.props.asset.key,
          this.formatAssetCoordinates(this.props),
        ),
      );
  }

  shouldComponentUpdate(nextProps, nextState) {
    return !!(nextState.socketSize.width && nextState.socketSize.height);
  }

  getOutputCoordinates = (center = true) => {
    let chidCoord = {};
    const { socketSize } = this.state;

    let x = this.outputStartPosition.x + (center ? socketSize.width * 0.5 : 0);
    let y = this.outputStartPosition.y + (center ? socketSize.height * 0.5 : 0);
    const xStart = x;

    Object.keys(this.props.asset.children).forEach((key, i) => {
      chidCoord[key] = { x, y };
      x += socketSize.width + this.outputSpacing.x;

      if (i == 3) {
        y += socketSize.height + this.outputSpacing.y;
        x = xStart;
      }
    });

    return chidCoord;
  };

  getInputCoordinates = () => {
    return [
      {
        x:
          this.inputSocketPos.x +
          (this.state.c14Img ? this.state.c14Img.width * 0.5 : 0),
        y:
          this.inputSocketPos.y +
          (this.state.c14Img ? this.state.c14Img.height * 0.5 : 0),
      },
    ];
  };

  render() {
    const { upsMonitorImg, c14Img } = this.state;

    const inputSocket = (
      <Image
        image={c14Img}
        x={this.inputSocketPos.x}
        y={this.inputSocketPos.y}
      />
    );
    const outputSockets = this.getOutputSockets(true);

    return (
      <Group
        x={this.props.x}
        y={this.props.y}
        ref="asset"
        draggable="true"
        onDragMove={this.updateAssetPos.bind(this)}
      >
        <Text
          x={230}
          y={-125}
          text={this.props.asset.name}
          fontSize={this.props.fontSize}
          fontFamily={'Helvetica'}
        />

        <AssetOutline
          path={paths.ups}
          onClick={this.handleClick.bind(this)}
          selected={this.props.selected}
        >
          <LEDDisplay
            x={345}
            y={-50}
            battery={this.props.asset.battery}
            status={!!this.props.asset.status}
            upsMonitorImg={upsMonitorImg}
          />
          {inputSocket}
        </AssetOutline>

        {outputSockets}
      </Group>
    );
  }
}
