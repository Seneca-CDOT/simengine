import React from 'react';
import { Text, Group, Path, Image, Rect } from 'react-konva';
import Socket from '../common/Socket';
import PropTypes from 'prop-types';
import c14 from '../../../images/c14.svg';
/**
 * Draw PDU graphics
 */
export default class Pdu extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      color: 'grey',
      selectedSocketKey: -1,
      x: props.x?props.x:40,
      y: props.y?props.y:40,
      c14: null
    };
    this.selectSocket = this.selectSocket.bind(this);
    this.inputSocketPos = {x: -70, y: 0};
  }

  componentDidMount() {
    const image = new window.Image();
    image.src = c14;
    image.onload = () => {
      this.setState({ c14: image });
    };
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

  getOutputCoordinates = () => {
    const childKeys = Object.keys(this.props.asset.children);
    const chidCoord = {};
    Object.keys(childKeys).map((e, i) => (chidCoord[childKeys[i]]={x: 100+(i*90) + this.state.c14.width*0.5, y: this.state.c14.height*0.5}));
    return chidCoord;
  }


  updatePduPos = (s) => {
    const coord = { 
      x: s.target.attrs.x, 
      y: s.target.attrs.y,
      inputCenterX: this.inputSocketPos.x + this.state.c14.width*0.5,
      inputCenterY: this.inputSocketPos.y + this.state.c14.height*0.5,
      outputConnections: this.getOutputCoordinates(),
    };

    this.setState(coord);
    this.props.onPosChange(this.props.assetId, coord);
  }

  render() {

    let sockets = [];
    const inputSocket = <Image image={this.state.c14} x={this.inputSocketPos.x} y={this.inputSocketPos.y}/>;

    let x=100;
    const pduName = this.props.asset.name ? this.props.asset.name:'pdu';
    const asset = this.props.asset;
    let load = Math.round(asset.load);
    load = load > 9?""+load:"0"+load;

    // Initialize outlets that are part of the PDU
    for (const ckey of Object.keys(asset.children)) {

      asset.children[ckey].name = `[${ckey}]`;
      sockets.push(
        <Socket
          x={x}
          y={0}
          key={ckey}
          onElementSelection={() => { this.selectSocket(ckey); }}
          selectable={true}
          draggable={false}
          asset={asset.children[ckey]}
          assetId={ckey}
          selected={this.state.selectedSocketKey === ckey && this.props.nestedComponentSelected}
          powered={this.props.asset.status !== 0}
          parentSelected={this.props.selected}
          onPosChange={this.props.onPosChange}
        />
      );
      x += 90;
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
          stroke={this.props.selected ? 'blue' : 'grey'}
          fill={'white'}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={this.handleClick.bind(this)}
        />
        <Text y={-85} text={pduName} fontSize={18}  fontFamily={'Helvetica'}/>
        <Group y={15} x={845}>
          <Rect width={60} height={60} fill={"#4d4d4d"} stroke={"black"}/>
          <Text y={10} x={5} text={load} fontFamily={'DSEG7Modern'} fontSize={30} fill={this.props.asset.status?'yellow':'grey'} />
          <Text y={65} x={8} text={"AMPS"} />
        </Group>
        {/* Draw Sockets */}
        {inputSocket}
        {sockets}
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
