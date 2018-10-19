import React from 'react';
import { Text, Group, Image } from 'react-konva';

// ** components
import Led from '../common/Led';
import PowerSupply from './PowerSupply';
import Asset from '../common/Asset';
import AssetOutline from '../common/AssetOutline';

// ** misc
import serverPlaceholderSource from '../../../images/server-front.svg';
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

  getOutputCoordinates = () => { return {}; }

  getInputCoordinates = (center=true) => {

    const childKeys = Object.keys(this.props.asset.children);
    const childCoord = {};

    const xPadding = this.state.psuSize.width;
    const yPadding = center?this.state.psuSize.height*0.5:0;

    Object.keys(childKeys).map((e, i) => (childCoord[childKeys[i]]={x: ((center?xPadding:50)+xPadding*i) + i*20, y: yPadding}));
    return center?Object.values(childCoord):childCoord;
  }

  /** Initialize Power Supplies */
  getInputPSUs = () => {
    
    let psus = [];
    const asset = this.props.asset;
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

    return psus;
  }


  render() {

    const psus = this.getInputPSUs();
    const { x, y, serverPlaceholderImg } = this.state;
    
    return (
      <Group draggable="true" onDragMove={this.updateAssetPos.bind(this)} x={x} y={y} ref="asset">

        {/* Draw Server as SVG path */}
        <AssetOutline path={paths.server} onClick={this.handleClick.bind(this)} selected={this.props.selected} />
        <Text y={-100} text={this.props.asset.name} fontSize={18}  fontFamily={'Helvetica'}/>
        
        {/* Draw Power Supplies */}
        {psus}

        {/* Draw some placeholder server-stuff */}
        <Image x={550} y={-20} image={serverPlaceholderImg} onClick={this.handleClick}/>

        {/* Machine status */}
        <Led socketOn={this.props.asset.status} powered={this.props.powered}/>
        
      </Group>
    );
  }
}
