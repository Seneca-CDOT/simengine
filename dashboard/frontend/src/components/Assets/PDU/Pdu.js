import React from 'react';
import PropTypes from 'prop-types';
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
      socketSize: {x:0, y:0},
      // graphics
      c14Img: null,
    };

    this.outputStartPosition = 100;
    this.outputSpacing = 90; // distance between out-sockets
  }

  componentDidMount () {
    this.loadImages({ c14Img: c14Source });
    Socket.socketSize().then((size) => { this.setState({ socketSize: size }); });
  }

  getOutputCoordinates = (center=true) => {
    const childKeys = Object.keys(this.props.asset.children);
    const chidCoord = {};

    const xPadding = this.outputStartPosition + (center?this.state.socketSize.height*0.5:0);
    const yPadding = center?this.state.socketSize.width*0.5:0;
    Object.keys(childKeys).map((e, i) => (chidCoord[childKeys[i]]={x: xPadding + (i*this.outputSpacing), y: yPadding}));
    return chidCoord;
  }

  getInputCoordinates = (center=true) => [{ x: (center?this.state.c14Img.width*0.5:0), y: (center?this.state.c14Img.height*0.5:0), }];

  render() {

    const {inX, inY} = this.getInputCoordinates(false)[0];
    
    const inputSocket = <Image image={this.state.c14Img} x={inX} y={inY}/>;
    const outputSockets = this.getOutputSockets();

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
