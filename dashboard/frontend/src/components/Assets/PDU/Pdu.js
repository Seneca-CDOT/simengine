import React from 'react';
import { Text, Group, Image } from 'react-konva';

// ** components
import Socket from '../common/Socket';
import OutputAsset from '../common/OutputAsset';
import AssetOutline from '../common/AssetOutline';
import LEDDisplay from './LEDDisplay';

// ** misc
import c14Source from '../../../images/c14.svg';
import paths from '../../../styles/paths';

/**
 * Draw PDU graphics
 */
export default class Pdu extends OutputAsset {
  constructor(props) {
    super(props);
    this.state = {
      socketSize: { width: 0, height: 0 },
      // graphics
      c14Img: null,
    };

    // set outlet properties
    this.outputSpacing = { x: 10, y: 0 };
    this.outputStartPosition = { x: 100, y: 0 };
  }

  componentDidMount() {
    Promise.all(this.loadImages({ c14Img: c14Source }))
      .then(Socket.socketSize)
      .then((size) => this.setState({ socketSize: size }))
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
    const childKeys = Object.keys(this.props.asset.children);
    const childCoord = {};

    const startPosX =
      this.outputStartPosition.x +
      (center ? this.state.socketSize.height * 0.5 : 0);
    const startPosY =
      this.outputStartPosition.y +
      (center ? this.state.socketSize.width * 0.5 : 0);

    Object.keys(childKeys).map(
      (e, i) =>
        (childCoord[childKeys[i]] = {
          x:
            startPosX +
            i * (this.state.socketSize.width + this.outputSpacing.x),
          y: startPosY,
        }),
    );
    return childCoord;
  };

  getInputCoordinates = (center = true) => [
    center && this.state.c14Img
      ? { x: this.state.c14Img.width * 0.5, y: this.state.c14Img.height * 0.5 }
      : { x: 0, y: 0 },
  ];

  render() {
    const { inX, inY } = this.getInputCoordinates(false)[0];
    const { c14Img } = this.state;

    const inputSocket = <Image image={c14Img} x={inX} y={inY} />;
    const outputSockets = this.getOutputSockets();

    return (
      <Group
        x={this.props.x}
        y={this.props.y}
        ref="asset"
        draggable="true"
        onDragMove={this.updateAssetPos.bind(this)}
      >
        <Text
          y={-85}
          text={this.props.asset.name}
          fontSize={this.props.fontSize}
          fontFamily={'Helvetica'}
        />

        {/* Draw PDU - SVG Path */}
        <AssetOutline
          path={paths.pdu}
          onClick={this.handleClick.bind(this)}
          selected={this.props.selected}
        >
          {/* PDU label & load LED */}
          <LEDDisplay
            load={Math.round(this.props.asset.load)}
            y={15}
            x={845}
            status={!!this.props.asset.status}
          />
          {inputSocket}
        </AssetOutline>

        {outputSockets}
      </Group>
    );
  }
}
