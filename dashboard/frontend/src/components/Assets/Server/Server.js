import React from 'react';
import { Text, Group, Path, Image } from 'react-konva';
import PropTypes from 'prop-types';
import Led from '../common/Led';
import PowerSupply from './PowerSupply';
import frontimg from '../../../images/server-front.svg';

import colors from '../../../styles/colors';
import paths from '../../../styles/paths';

/**
 * Draw Server graphics
 */
export default class Server extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      selectedPsuKey: -1,
      x: props.x,
      y: props.y,
      psuSize: {x:0, y:0},

      serverPlaceholderImg: null
    };
    
    this.selectPSU = this.selectPSU.bind(this);
  }

  componentDidMount() {
    const serverPlaceholderImg = new window.Image();
    serverPlaceholderImg.src = frontimg;
    serverPlaceholderImg.onload = () => { this.setState({ serverPlaceholderImg });};
    PowerSupply.psuSize().then((size) => {
      this.setState({ psuSize: size });
    });
  }


  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.server.setZIndex(100);
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

  /** Notify top-lvl Component that on of the PSUs was selected*/
  selectPSU = (ckey) => {
    this.setState({ selectedPsuKey: ckey });
    this.props.onElementSelection(ckey, this.props.asset.children[ckey]);
  }

  getInputCoordinates = (center=true) => {

    const childKeys = Object.keys(this.props.asset.children);
    const chidCoord = {};

    const xPadding = this.state.psuSize.width;
    const yPadding = center?this.state.psuSize.height*0.5:0;

    Object.keys(childKeys).map((e, i) => (chidCoord[childKeys[i]]={x: ((center?xPadding:50)+xPadding*i) + i*20, y: yPadding}));
    return chidCoord;
  }

  updateServerPos = (s) => {
    const coord = {
      x: s.target.attrs.x,
      y : s.target.attrs.y,
      inputConnections: Object.values(this.getInputCoordinates()),
      outputConnections: []
    };

    this.setState(coord);
    this.props.onPosChange(this.props.assetId, coord);
  }

  render() {

    let psus = [];

    const serverName = this.props.asset.name ? this.props.asset.name:'ups';
    const asset = this.props.asset;

    // Initialize Power Supplies
    const inputCoord = this.getInputCoordinates(false);

    for (const ckey of Object.keys(inputCoord)) {
      asset.children[ckey].name = `[${ckey}]`;
      psus.push(
        <PowerSupply
          x={inputCoord[ckey].x}
          y={inputCoord[ckey].y}
          key={ckey}
          onElementSelection={() => { this.selectPSU(ckey); }}
          draggable={false}
          asset={asset.children[ckey]}
          assetId={ckey}
          selected={this.state.selectedPsuKey === ckey && this.props.nestedComponentSelected}
          powered={this.props.powered}
          parentSelected={this.props.selected}
        />
      ); 
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
        <Path data={paths.server}
          strokeWidth={0.4}
          stroke={this.props.selected ? colors.selectedAsset : colors.deselectedAsset}
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
            image={this.state.serverPlaceholderImg}
            x={550}
            y={-20}
            onClick={this.handleClick}
        />

        {/* Machine status */}
        <Led socketOn={this.props.asset.status} powered={this.props.powered}/>
        
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
