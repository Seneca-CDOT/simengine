import React from 'react';
import { Text, Group, Image } from 'react-konva';
import Socket from '../common/Socket';
import PropTypes from 'prop-types';
import c14 from '../../../images/c14.svg';

import Asset from '../common/Asset';
import AssetOutline from '../common/AssetOutline';
import LEDDisplay from './LEDDisplay';

import paths from '../../../styles/paths';

/**
 * Draw PDU graphics
 */
export default class Pdu extends Asset {

  constructor(props) {
    super(props);
    this.state = {
      socketSize: {x:0, y:0},
      // graphics
      c14: null,
      // selected child
      selectedSocketKey: -1,
    };

    this.selectSocket = this.selectSocket.bind(this);
  }

  componentDidMount () {
    const image = new window.Image();
    image.src = c14;
    image.onload = () => {
      this.setState({ c14: image });
    };

    Socket.socketSize().then((size) => {
      this.setState({ socketSize: size });
    });
  }

  /** Notify top-lvl Component that PDU-Outlet was selected*/
  selectSocket = (ckey) => {
    this.setState({ selectedSocketKey: ckey });
    this.props.onElementSelection(ckey, this.props.asset.children[ckey]);
  }

  getOutputCoordinates = (center=true) => {
    const childKeys = Object.keys(this.props.asset.children);
    const chidCoord = {};
    const xPadding = center?this.state.socketSize.height*0.5:0;
    const yPadding = center?this.state.socketSize.width*0.5:0;
    Object.keys(childKeys).map((e, i) => (chidCoord[childKeys[i]]={x: 100+(i*90) + xPadding, y: yPadding}));
    return chidCoord;
  }

  getInputCoordinates = (center=true) => [{ x: (center?this.state.c14.width*0.5:0), y: (center?this.state.c14.height*0.5:0), }];

  render() {

    let outputSockets = [];

    const {inX, inY} = this.getInputCoordinates(false)[0];
    const inputSocket = <Image image={this.state.c14} x={inX} y={inY}/>;

    // Initialize outlets that are parts of the PDU
    const outputCoord = this.getOutputCoordinates(false);

    for (const ckey of Object.keys(outputCoord)) {
      this.props.asset.children[ckey].name = `[${ckey}]`;
      outputSockets.push(
        <Socket
          x={outputCoord[ckey].x}
          y={outputCoord[ckey].y}
          asset={this.props.asset.children[ckey]}
          assetId={ckey}
          key={ckey}

          onElementSelection={() => { this.selectSocket(ckey); }}
          onPosChange={this.props.onPosChange}

          selected={this.state.selectedSocketKey === ckey && this.props.nestedComponentSelected}
          powered={this.props.asset.status !== 0}
          parentSelected={this.props.selected}
        />
      ); 
    }

    return (
      <Group
        draggable="true"
        onDragMove={this.updateAssetPos.bind(this)}
        x={this.state.x}
        y={this.state.y}
        ref="asset"
      >

        {/* Draw PDU - SVG Path */}
        <AssetOutline path={paths.pdu} onClick={this.handleClick.bind(this)} selected={this.props.selected} />

        {/* PDU label */}
        <Text y={-85} text={this.props.asset.name} fontSize={18}  fontFamily={'Helvetica'}/>

        {/* LED display (load) */}
        <LEDDisplay load={Math.round(this.props.asset.load)} y={15} x={845} status={this.props.asset.status}/>

        {/* Draw Sockets (input connector and output outlets) */}
        {inputSocket}
        {outputSockets}

      </Group>
    );
  }
}

Pdu.propTypes = {
  nestedComponentSelected: PropTypes.bool.isRequired, // One of the PDU outlets are selected
};
