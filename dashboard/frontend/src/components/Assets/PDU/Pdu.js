import React from 'react';
import { Text, Group, Path, Image, Rect } from 'react-konva';
import Socket from '../common/Socket';
import PropTypes from 'prop-types';
import c14 from '../../../images/c14.svg';

import colors from '../../../styles/colors';

/**
 * Draw PDU graphics
 */
export default class Pdu extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      // coordinates
      x: props.x,
      y: props.y,
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

  componentWillReceiveProps(newProps) {
    this.setState({ x: newProps.x, y: newProps.y });
  }

  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.pdu.setZIndex(100);
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

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

  getInputCoordinates = (center=true) => {
    return [
      {
        x: (center?this.state.c14.width*0.5:0),
        y: (center?this.state.c14.height*0.5:0),
      }
    ];
  }

 /** returns global asset position (x, y), relative output & input outlet coordinates */
  updatePduPos = (s) => {
    const coord = {
      x: s.target.attrs.x,
      y: s.target.attrs.y,
      inputConnections: this.getInputCoordinates(),
      outputConnections: this.getOutputCoordinates(),
    };

    this.setState(coord);
    this.props.onPosChange(this.props.assetId, coord);
  }

  render() {

    let outputSockets = [];

    const {inX, inY} = this.getInputCoordinates(false)[0];
    const inputSocket = <Image image={this.state.c14} x={inX} y={inY}/>;

    const pduName = this.props.asset.name ? this.props.asset.name:'pdu';
    const asset = this.props.asset;
    let load = Math.round(asset.load);
    load = load > 9?""+load:"0"+load;

    // Initialize outlets that are parts of the PDU
    const outputCoord = this.getOutputCoordinates(false);

    for (const ckey of Object.keys(outputCoord)) {
      asset.children[ckey].name = `[${ckey}]`;
      outputSockets.push(
        <Socket
          x={outputCoord[ckey].x}
          y={outputCoord[ckey].y}
          asset={asset.children[ckey]}
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
        onDragMove={this.updatePduPos.bind(this)}
        x={this.state.x}
        y={this.state.y}
        ref="pdu"
      >

        {/* Draw PDU - SVG Path */}
        <Path data={"M -27.214914,140.21439 H 253.08991 c 1.86045,0 3.3582,1.41492 3.3582,3.17248 v 21.85487 c 0,1.75755 -1.49775,3.17248 -3.3582,3.17248 H -27.214914 c -1.860445,0 -3.358203,-1.41493 -3.358203,-3.17248 v -21.85487 c 0,-1.75756 1.497758,-3.17248 3.358203,-3.17248 z M -5.9971812,128.5323 H 231.87216 l 22.22631,11.70857 H -28.223485 Z"}
          strokeWidth={0.4}
          stroke={this.props.selected ? colors.selectedAsset : colors.deselectedAsset}
          fill={'white'}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={this.handleClick.bind(this)}
        />

        {/* PDU label */}
        <Text y={-85} text={pduName} fontSize={18}  fontFamily={'Helvetica'}/>

        {/* LED display (load) */}
        <Group y={15} x={845}>
          <Rect width={60} height={60} fill={colors.ledBackground} stroke={colors.ledStroke}/>
          <Text 
            y={10} 
            x={5} 
            text={load} 
            fontFamily={'DSEG7Modern'} 
            fontSize={30} 
            fill={this.props.asset.status?colors.ledText:colors.ledStatusOff} 
          />
          <Text y={65} x={8} text={"AMPS"} />
        </Group>

        {/* Draw Sockets (input connector and output outlets) */}
        {inputSocket}
        {outputSockets}

      </Group>
    );
  }
}

Pdu.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  onPosChange: PropTypes.func.isRequired, // called on PDU position change
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
  name: PropTypes.string,
  asset: PropTypes.object.isRequired, // Asset Details
  assetId: PropTypes.string.isRequired, // Asset Key
  selected: PropTypes.bool.isRequired, // Asset Selected by a user
  onElementSelection: PropTypes.func.isRequired, // Notify parent component of selection
  nestedComponentSelected: PropTypes.bool.isRequired, // One of the PDU outlets are selected
};
