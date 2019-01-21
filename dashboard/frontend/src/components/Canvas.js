import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Layer, Line } from 'react-konva';

import { Server, Pdu, Ups, Socket, Lamp } from './Assets';

import colors from '../styles/colors';


class Canvas extends Component {

  // map asset types to react components
  assetMap = {
    'outlet': Socket,
    'staticasset': Socket,
    'server': Server,
    'serverwithbmc': Server,
    'pdu': Pdu,
    'ups': Ups,
    'lamp': Lamp,
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
      isComponent: false,
      powered: false,
      x: asset.x,
      y: asset.y,
    };

    // check if upstream power source is present
    const upstreamPowered = (x) => this.props.getAssetByKey(x.key).status != 0;
    elementProps['powered'] = asset.parent?(asset.parent.find(upstreamPowered) !== undefined):(true);
  
    // select child elements
    if ('children' in asset) {
      elementProps['nestedComponentSelected'] = this.props.selectedAssetKey in asset.children;
    }

    return React.createElement(ReactElement, elementProps);
  }


  render() {
    const { assets, connections } = this.props;

    // asset drawings & their connections
    let systemLayout = [];
    let wireDrawing = [];

    if (assets) {
      // Initialize HA system layout
      for (const key of Object.keys(assets)) {
        systemLayout.push(this.getAssetComponent(this.assetMap[assets[key].type], assets[key]));
      }

      // draw wires
      for (const key of Object.keys(connections)) {
        const asset = this.props.getAssetByKey(key);

        wireDrawing.push(
          <Line
            points={Object.values(connections[key])}
            stroke={asset.status===1?colors.green:"grey"}
            strokeWidth={5}
            zIndex={300}
            key={`${key}${connections[key].destKey}`}
          />
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
  assets: PropTypes.object,
  connections: PropTypes.object,
  selectedAssetKey: PropTypes.number, 
  onPosChange: PropTypes.func.isRequired, // called on element dragged
  onElementSelection: PropTypes.func.isRequired, // called when asset is selected
  getAssetByKey: PropTypes.func.isRequired, // retrieve asset props by key
};

export default Canvas;
