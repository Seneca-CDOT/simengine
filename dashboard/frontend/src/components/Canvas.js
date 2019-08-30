import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Layer, Line } from 'react-konva';

import { Server, Pdu, Ups, Socket, Lamp } from './Assets';

import colors from '../styles/colors';

/**
 * Displays hardware components (assets) as well as their connections
 */
class Canvas extends Component {
  // map asset types to react components
  assetMap = {
    outlet: Socket,
    staticasset: Socket,
    server: Server,
    serverwithbmc: Server,
    pdu: Pdu,
    ups: Ups,
    lamp: Lamp,
  };

  getAssetComponent(ReactElement, asset) {
    /**Render asset element (on of the components defined in 'assetMap') */

    // asset props
    let elementProps = {
      onPosChange: this.props.onPosChange.bind(this),
      onElementSelection: this.props.onElementSelection.bind(this),
      key: asset.key,
      asset: asset,
      selected: this.props.selectedAssetKey === asset.key,
      x: asset.x,
      y: asset.y,
      fontSize: this.props.labelFontSize,
    };

    // check if upstream power source is present
    const upstreamPowered = x => this.props.getAssetByKey(x.key).status != 0;
    elementProps['powered'] = asset.parent
      ? asset.parent.find(upstreamPowered) !== undefined
      : true;

    // select child elements
    if ('children' in asset) {
      elementProps['nestedComponentSelected'] =
        this.props.selectedAssetKey in asset.children;
    }

    return React.createElement(ReactElement, elementProps);
  }

  render() {
    const { assets, connections, wireWidth, wireZIndex } = this.props;

    // asset drawings & their connections
    let systemLayout = [];
    let wireDrawing = [];

    if (assets) {
      // Initialize HA system layout
      for (const key of Object.keys(assets)) {
        systemLayout.push(
          this.getAssetComponent(this.assetMap[assets[key].type], assets[key]),
        );
      }

      // draw wires
      for (const key of Object.keys(connections)) {
        const asset = this.props.getAssetByKey(key);
        const linePoints = Object.values(connections[key]).filter(
          n => typeof n === 'number',
        );

        wireDrawing.push(
          <Line
            points={linePoints}
            stroke={asset.status === 1 ? colors.green : colors.grey}
            strokeWidth={wireWidth}
            zIndex={wireZIndex}
            key={`${key}${connections[key].destKey}`}
            shadowBlur={3}
          />,
        );
      }
    }

    return (
      <Layer>
        {systemLayout}
        {wireDrawing}
      </Layer>
    );
  }
}

Canvas.propTypes = {
  /** hardware components of the layout */
  assets: PropTypes.object,
  /** represents wirings between assets */
  connections: PropTypes.object,
  /** key of the selected asset */
  selectedAssetKey: PropTypes.number,
  /** font size for asset labels */
  labelFontSize: PropTypes.number,
  /** width of the wiring (in px) */
  wireWidth: PropTypes.number,
  /** z-index of the wirings */
  wireZIndex: PropTypes.number,
  /** called when any of the assets is moved/dragged */
  onPosChange: PropTypes.func.isRequired,
  /** called when any of the assets is selected */
  onElementSelection: PropTypes.func.isRequired,
  /** retrieve asset props by key */
  getAssetByKey: PropTypes.func.isRequired,
};

Canvas.defaultProps = {
  labelFontSize: 18,
  wireWidth: 5,
  wireZIndex: 300,
};

export default Canvas;
