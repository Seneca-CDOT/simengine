import React from 'react';
import { Text, Group, Path, Image } from 'react-konva';
import PropTypes from 'prop-types';
import SocketStatus from '../common/SocketStatus';
import PowerSupply from './PowerSupply';
import frontimg from '../../../images/server-front.svg';
/**
 * Draw Server graphics
 */
export default class Server extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      color: 'grey',
      selectedPsuKey: -1,
      x: props.x?props.x:40,
      y: props.y?props.y:40,
      frontimg: null
    };
    this.selectSocket = this.selectSocket.bind(this);
  }

  componentDidMount() {
    const image = new window.Image();
    image.src = frontimg;
    image.onload = () => {
      // setState will redraw layer
      // because "image" property is changed
      this.setState({ frontimg: image });
    };

  }

  componentWillReceiveProps(nextProps) {
    this.setState({ x: nextProps.x, y: nextProps.y });
  }

  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.server.setZIndex(100);
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

  /** Notify top-lvl Component that PDU-Outlet was selected*/
  selectSocket = (ckey) => {
    this.setState({ selectedPsuKey: ckey });
    this.props.onElementSelection(ckey, this.props.asset.children[ckey]);
  }

  updateServerPos = (s) => {
    this.setState({ x: s.target.attrs.x, y : s.target.attrs.y });
    this.props.onPosChange(this.props.assetId, s);
  }

  render() {

    let psus = [];
    // const inputSocket = <Socket x={-70} socketName={"input socket"} selectable={false} draggable={false}/>;

    let x=50;
    const serverName = this.props.asset.name ? this.props.asset.name:'ups';
    const asset = this.props.asset;

    // Initialize Powe Supplies
    for (const ckey of Object.keys(asset.children)) {

      asset.children[ckey].name = `[${ckey}]`;
      psus.push(
        <PowerSupply
          x={x}
          key={ckey}
          onElementSelection={() => { this.selectSocket(ckey); }}
          selectable={true}
          draggable={false}
          asset={asset.children[ckey]}
          assetId={ckey}
          selected={this.state.selectedPsuKey === ckey && this.props.nestedComponentSelected}
          powered={this.props.powered}
          parentSelected={this.props.selected}
        />
      );
      x += 240;
    }
    return (
      <Group
        draggable="true"
        onDragMove={this.updateServerPos.bind(this)}
        x={this.state.x}
        y={this.state.y}
        ref="server"
      >


        {/* Draw Server as SVG path */}
        <Path data={"m 7.84681,135.86767 h 194.30638 c 1.28966,0 2.3279,1.85111 2.3279,4.15049 v 28.5923 c 0,2.29937 -1.03824,4.15049 -2.3279,4.15049 H 7.84681 c -1.289654,0 -2.327895,-1.85112 -2.327895,-4.15049 v -28.5923 c 0,-2.29938 1.038241,-4.15049 2.327895,-4.15049 z M 22.554872,124.18558 H 187.44512 l 15.40721,11.70857 H 7.147672 Z"}
          strokeWidth={0.4}
          stroke={this.props.selected ? 'blue' : 'grey'}
          fill={'white'}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={this.handleClick.bind(this)}
        />

        <Text y={-100} text={serverName} fontSize={18}  fontFamily={'Helvetica'}/>
        {/* Draw Power Supplies */}
        {psus}

        {/* Draw some placeholder server-stuff */}
        <Image
            image={this.state.frontimg}
            x={550}
            y={-20}
            onClick={this.handleClick}
        />
         <SocketStatus socketOn={this.props.asset.status} powered={this.props.powered}/>
      </Group>
    );
  }
}

Server.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  onPosChange: PropTypes.func.isRequired, // called on asset position change
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
  name: PropTypes.string,
  asset: PropTypes.object.isRequired, // Asset Details
  assetId: PropTypes.string.isRequired, // Asset Key
  selected: PropTypes.bool.isRequired, // Asset Selected by a user
  onElementSelection: PropTypes.func.isRequired, // Notify parent component of selection
  nestedComponentSelected: PropTypes.bool.isRequired, // One of the powerSupplies are selected
};
