import React from 'react';
import { Text, Group, Path } from 'react-konva';
import Socket from '../common/Socket';
import PropTypes from 'prop-types';

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
      y: props.y?props.y:40
    };
    this.selectSocket = this.selectSocket.bind(this);
  }

  /** Notify Parent of Selection */
  handleClick = () => {
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

  /** Notify top-lvl Component that PDU-Outlet was selected*/
  selectSocket = (ckey) => {
    this.setState({ selectedSocketKey: ckey });
    this.props.onElementSelection(ckey, this.props.asset.children[ckey]);
  }

  updatePduPos = (s) => {
    this.setState({ x: s.target.attrs.x, y : s.target.attrs.y });
    this.props.onPosChange(this.props.assetId, s);
  }

  render() {

    let sockets = [];
    const inputSocket = <Socket x={-70} socketName={"input socket"} selectable={false} draggable={false}/>;

    let x=100;
    const pduName = this.props.asset.name ? this.props.asset.name:'pdu';
    const asset = this.props.asset;

    // Initialize outlets that are part of the PDU
    for (const ckey of Object.keys(asset.children)) {

      asset.children[ckey].name = `[${ckey}]`;
      sockets.push(
        <Socket
          x={x}
          key={ckey}
          onElementSelection={() => { this.selectSocket(ckey); }}
          selectable={true}
          draggable={false}
          asset={asset.children[ckey]}
          assetId={ckey}
          selected={this.state.selectedSocketKey === ckey && this.props.pduSocketSelected}
          powered={this.props.asset.status}
          parentSelected={this.props.selected}
          red_means_on={true}
        />
      );
      x += 90;
    }

    return (
      <Group
        draggable="true"
        onDragMove={this.updatePduPos.bind(this)}
      >


        {/* Draw PDU - SVG Path */}
        <Path data={"M -7.357125,128.5323 H 217.35711 l 20.99711,11.70857 H -28.354227 Z M -27.401434,140.21439 H 237.40143 c 1.75756,0 3.17248,1.41492 3.17248,3.17248 v 21.85487 c 0,1.75755 -1.41492,3.17248 -3.17248,3.17248 H -27.401434 c -1.757555,0 -3.172481,-1.41493 -3.172481,-3.17248 v -21.85487 c 0,-1.75756 1.414926,-3.17248 3.172481,-3.17248 z"}
          strokeWidth={0.4}
          stroke={this.props.selected ? 'blue' : 'grey'}
          fill={'white'}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={this.handleClick.bind(this)}
        />

        <Text y={-85} text={pduName} />
        {/* Draw Sockets */}
        {inputSocket}
        {sockets}
      </Group>
    );
  }
}

Pdu.propTypes = {
  name: PropTypes.string,
  asset: PropTypes.object.isRequired, // Asset Details
  assetId: PropTypes.string.isRequired, // Asset Key
  selected: PropTypes.bool.isRequired, // Asset Selected by a user
  onElementSelection: PropTypes.func.isRequired, // Notify parent component of selection
  pduSocketSelected: PropTypes.bool.isRequired, // One of the PDU outlets are selected
};
