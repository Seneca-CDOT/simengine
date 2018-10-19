
import React from 'react';
import { Text, Group, Image } from 'react-konva';

import upsMonitorSource from '../../../images/ups_monitor_2.png';
import c14Source from '../../../images/c14.svg';
// import Socket from '../common/Socket';

import OutputAsset from '../common/OutputAsset';
import AssetOutline from '../common/AssetOutline';
import LEDDisplay from './LEDDisplay';

import paths from '../../../styles/paths';

/**
 * Draw Ups graphics
 */
export default class Ups extends OutputAsset {

  constructor(props) {
    super(props);
    this.state = {
      upsMonitorImg: null,
      c14Img: null
    };

    this.inputSocketPos = {x: 254, y: 5};
  }

  componentDidMount() {
    this.loadImages({ upsMonitorImg: upsMonitorSource, c14Img: c14Source }); 
  }

  getOutputCoordinates = (center=true) => {

    let chidCoord = {};
    let x = 250 + this.state.c14Img&&center?this.state.c14Img.width*0.5:0;
    let y = 150 + this.state.c14Img&&center?this.state.c14Img.height*0.5:0;

    Object.keys(this.props.asset.children).forEach((key, i) => {
      chidCoord[key] = {x, y};
      x += 100;

      if (i == 3) {
        y += 100;
        x = 250;
      }
    });

    return chidCoord;
  }

  getInputCoordinates = () => {
    return  [
      {
        x: this.inputSocketPos.x + this.state.c14Img?this.state.c14Img.width*0.5:0,
        y: this.inputSocketPos.y + this.state.c14Img?this.state.c14Img.height*0.5:0,
      }
    ];
  } 

  render() {

    const {upsMonitorImg} = this.state;
    const inputSocket = <Image image={this.state.c14Img} x={this.inputSocketPos.x} y={this.inputSocketPos.y}/>;

    const upsName = this.props.asset.name ? this.props.asset.name:'ups';
    // let chargeBar = "|||||||||||||||||||||||||||||||||||";
    // chargeBar = this.props.asset.battery === 1000 ? chargeBar: chargeBar.substring(chargeBar.length * (1-this.props.asset.battery * 0.001));

    const outputSockets = this.getOutputSockets();

    return (
      <Group
        draggable="true"
        onDragMove={this.updateAssetPos.bind(this)}
        x={this.state.x}
        y={this.state.y}
        ref="asset"
      >

        {/* Draw Ups as SVG path */}
        <AssetOutline path={paths.ups} onClick={this.handleClick.bind(this)} selected={this.props.selected} />

        {/* UPS Label */}
        <Text y={-125} x={230} text={upsName} fontSize={18}  fontFamily={'Helvetica'} />

        {/* UPS Display */}
        <LEDDisplay battery={this.props.asset.battery} y={-50} x={345} status={this.props.asset.status} upsMonitorImg={upsMonitorImg}/>

          {/* <Image image={this.state.upsMonitorImg}/>
          <Group y={50} x={18}>
            <Text
              text={`Output ${this.props.asset.status?'ON':'OFF'}`}
              fontFamily={'DSEG14Modern'}
              fontSize={16}
              fill={this.props.asset.status?'white':'grey'}
            />

            <Text y={30}
              text={`Batt ${Math.floor(this.props.asset.battery/10)}%`}
              fontFamily={'DSEG14Modern'}
              fontSize={16}
              fill={this.props.asset.status?'white':'grey'}
            />
            <Text y={30} x={110}
              text={chargeBar}

              fontSize={16}
              fill={this.props.asset.status?'white':'grey'}
            />
          </Group>
        </Group> */}
        
        {/* IO Sockets */}
        {outputSockets}
        {inputSocket}


      </Group>
    );
  }
}
