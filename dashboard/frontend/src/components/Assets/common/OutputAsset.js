import React from 'react';
import PropTypes from 'prop-types';

import Asset from './Asset';
import Socket from './Socket';

/** Output asset provides output outlet(s) */
class OutputAsset extends Asset {
  constructor(props) {
    super(props);
    this.state = {
      // selected child
      selectedSocketKey: -1,
    };

    this.outputSpacing = { x: 0, y: 0 };
    this.outputStartPosition = { x: 0, y: 0 };

    this.selectSocket.bind(this);
  }

  /** Notify top-lvl Component that OUT-outlet was selected*/
  selectSocket = ckey => {
    this.setState({ selectedSocketKey: ckey });
    this.props.onElementSelection(this.props.asset.children[ckey]);
  };

  getOutputSockets = (hideName = false) => {
    // Initialize outlets that are parts of the PDU
    const outputCoord = this.getOutputCoordinates(false);
    let outputSockets = [];

    for (const ckey of Object.keys(outputCoord)) {
      this.props.asset.children[ckey].name = `[${ckey}]`;
      outputSockets.push(
        <Socket
          x={outputCoord[ckey].x}
          y={outputCoord[ckey].y}
          asset={this.props.asset.children[ckey]}
          key={ckey}
          onElementSelection={() => {
            this.selectSocket(ckey);
          }}
          onPosChange={this.props.onPosChange}
          hideName={hideName}
          isComponent={true}
          selected={
            this.state.selectedSocketKey === ckey &&
            this.props.nestedComponentSelected
          }
          powered={this.props.asset.status !== 0}
          parentSelected={this.props.selected}
        />,
      );
    }

    return outputSockets;
  };
}

OutputAsset.defaultProps = {
  nestedComponentSelected: false,
};

OutputAsset.propTypes = {
  nestedComponentSelected: PropTypes.bool.isRequired, // Display outlet name
};

export default OutputAsset;
