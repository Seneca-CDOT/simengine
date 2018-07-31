
import React from 'react';
import { Text, Group, Path, Image, Rect } from 'react-konva';
import PropTypes from 'prop-types';

import ups_monitor from '../../../images/ups_monitor.png';
import c14 from '../../../images/c14.svg';
import Socket from '../common/Socket';

/**
 * Draw Ups graphics
 */
export default class Ups extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      color: 'grey',
      selectedSocketKey: -1,
      x: props.x?props.x:40,
      y: props.y?props.y:40,
      ups_monitor: null,
      c14: null
    };
    this.selectSocket = this.selectSocket.bind(this);
  }

  componentDidMount() {
    const upsMonitorImg = new window.Image();
    const c14Img = new window.Image();

    upsMonitorImg.src = ups_monitor;
    upsMonitorImg.onload = () => {
      // setState will redraw layer
      // because "upsMonitorImg" property is changed
      this.setState({ ups_monitor: upsMonitorImg });
    };

    c14Img.src = c14;
    c14Img.onload = () => {
      // setState will redraw layer
      // because "c14Img" property is changed
      this.setState({ c14: c14Img });
    };

  }

  componentWillReceiveProps(nextProps) {
    this.setState({ x: nextProps.x, y: nextProps.y });
  }

  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.ups.setZIndex(100);
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

  /** Notify top-lvl Component that PDU-Outlet was selected*/
  selectSocket = (ckey) => {
    this.setState({ selectedSocketKey: ckey });
    this.props.onElementSelection(ckey, this.props.asset.children[ckey]);
  }

  updateUpsPos = (s) => {
    this.setState({ x: s.target.attrs.x, y : s.target.attrs.y });
    this.props.onPosChange(this.props.assetId, s);
  }

  render() {

    let sockets = [];
    // const inputSocket = <Socket x={-70} socketName={"input socket"} selectable={false} draggable={false}/>;
    const inputSocket = <Image image={this.state.c14} x={370} y={175}/>;
    //let x=50;
    const upsName = this.props.asset.name ? this.props.asset.name:'ups';
    const asset = this.props.asset;
    let y=10;
    let x=5;
    let socketIndex = 0;
    // Initialize outlets that are part of the PDU
    for (const ckey of Object.keys(asset.children)) {

      asset.children[ckey].name = `[${ckey}]`;
      sockets.push(
        <Socket
          y={y}
          x={x}
          key={ckey}
          onElementSelection={() => { this.selectSocket(ckey); }}
          selectable={true}
          draggable={false}
          asset={asset.children[ckey]}
          assetId={ckey}
          selected={this.state.selectedSocketKey === ckey && this.props.nestedComponentSelected}
          powered={this.props.asset.status}
          parentSelected={this.props.selected}
          hideName={true}
          onPosChange={this.props.onPosChange}
        />
      );
      y += 100;
      socketIndex++;
      if (socketIndex == 4) {
        x += 100;
        y = 10;
      }
    }


    return (
      <Group
        draggable="true"
        onDragMove={this.updateUpsPos.bind(this)}
        x={this.state.x}
        y={this.state.y}
        ref="ups"
      >


        {/* Draw Ups as SVG path */}
        <Path data={"M 51.551168,118.02771 H 161.85062 l 10.30629,7.10992 H 41.244884 Z M 41.225275,125.12154 H 172.17651 c 0.86917,0 1.56887,5.60194 1.56887,12.56046 v 86.52769 c 0,6.95848 -0.6997,12.56045 -1.56887,12.56045 H 41.225275 c -0.869151,0 -1.568866,-5.60197 -1.568866,-12.56045 V 137.682 c 0,-6.95852 0.699715,-12.56046 1.568866,-12.56046 z"}
          strokeWidth={0.4}
          stroke={this.props.selected ? 'blue' : 'grey'}
          fill={'white'}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={this.handleClick.bind(this)}
        />
        <Group
         x={480}
         y={-60}
        >
          <Rect
            ref="rect"
            width="90"
            height="410"
            fill="white"
            stroke={this.props.selected ? 'blue' : 'grey'}
            strokeWidth={1.4}
          />

          <Rect
            ref="rect"
            width="90"
            height="410"
            fill="white"
            stroke={this.props.selected ? 'blue' : 'grey'}
            strokeWidth={1.4}
            x={100}
          />
          {sockets}
        </Group>


        <Text y={-125} x={230} text={upsName} />
        <Group
          x={200}
          y={-20}
        >
          <Image
              image={this.state.ups_monitor}
              onClick={this.handleClick}
          />

          <Text y={112} x={18}
            text={"Output Off"}
            fontFamily={'DSEG14Modern'}
            fontSize={11}
            fill={this.props.asset.status?'white':'grey'}
          />

          <Text y={135} x={18}
            text={"Batt 100%"}
            fontFamily={'DSEG14Modern'}
            fontSize={11}
            fill={this.props.asset.status?'white':'grey'}
          />
          <Text y={135} x={115}
            text={"|||||||||||||||||||||||||||||||||||"}

            fontSize={11}
            fill={this.props.asset.status?'white':'grey'}
          />
        </Group>


        {/* Input Socket */}
        {inputSocket}

      </Group>
    );
  }
}

Ups.propTypes = {
  name: PropTypes.string,
  asset: PropTypes.object.isRequired, // Asset Details
  assetId: PropTypes.string.isRequired, // Asset Key
  selected: PropTypes.bool.isRequired, // Asset Selected by a user
  onElementSelection: PropTypes.func.isRequired, // Notify parent component of selection
  nestedComponentSelected: PropTypes.bool.isRequired, // One of the UPS outlets are selected
};
