import React from 'react';
import { Text, Group, Path, Image } from 'react-konva';

// ** components
import Led from '../common/Led';
import PowerSupply from './PowerSupply';
import Asset from '../common/Asset';

// ** misc
import serverPlaceholderSource from '../../../images/server-front.svg';
import colors from '../../../styles/colors';
import paths from '../../../styles/paths';

/**
 * Draw Server graphics
 */
export default class Server extends Asset {

  constructor(props) {
    super(props);
    this.state = {
      selectedPsuKey: -1,
      psuSize: {x:0, y:0},

      serverPlaceholderImg: null
    };
    
    this.selectPSU = this.selectPSU.bind(this);
  }

  componentDidMount() {
    this.loadImages({ serverPlaceholderImg: serverPlaceholderSource });
    PowerSupply.psuSize().then((size) => { this.setState({ psuSize: size }); });
  }

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
        ref="asset"
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
