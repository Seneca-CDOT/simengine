
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import socket from '../../../images/socket.svg';
import SocketStatus from './SocketStatus';
import PropTypes from 'prop-types';
/* eslint-disable */

/**
 * Outlet Graphics
 */
export default class Socket extends React.Component {

    constructor(props) {
      super();
      this.state = {
        image: null,
        color: 'grey',
        x: props.x?props.x:40, // TODO: change to default
        y: props.y?props.y:0,
        bgImage: null,
      };

      if (props.asset && 'imgUrl' in props.asset) {
        const bgImage = new window.Image();
        bgImage.src = props.asset.imgUrl;
        bgImage.onload = () => {

          const oldHeight = bgImage.height;
          bgImage.height = 160;
          bgImage.width = bgImage.width / (oldHeight/160);

          this.setState({
            bgImage: bgImage
          });
        };
      }
    }

    /** Load Socket Image */
    componentDidMount() {
      const image = new window.Image();
      image.src = socket;
      image.onload = () => {
        // setState will redraw layer
        // because "image" property is changed

        this.setState({
          image: image
        });
      };
    }

    // componentWillUpdate(newProps) {
    //   // console.log("xxxxxxxxxxxxxxxxxxx")
    //   // console.log(this.props.assetId)
    //   // console.log({ x: newProps.x, y: newProps.y })
    //   // console.log({ x: this.props.x, y:  this.props.y })
    //   if (newProps.x != this.props.x || newProps.y != this.props.y) {
    //     const coord = { x: newProps.x, y: newProps.y };
    //     this.props.onPosChange(this.props.assetId, coord);
    //   }

    // }

    // componentWillReceiveProps(newProps) {

    //   //this.setState({ x: newProps.x, y: newProps.y });
    //   console.log("xxxxxxxxxxxxxxxxxxx")
    //   console.log(this.props.assetId)
    //   console.log({ x: newProps.x, y: newProps.y })
    //   console.log({ x: this.state.x, y:  this.state.y })
    //   const coord = { x: newProps.x, y: newProps.y };
    //   // this.props.onPosChange(this.props.assetId, coord);
    //   // if (newProps.x != this.state.x || newProps.y != this.state.y) {
    //   //   const coord = { x: newProps.x, y: newProps.y };
    //   //   this.setState(coord);
    //   //   this.props.onPosChange(this.props.assetId, coord);
    //   // }

    // }

     /** Notify Parent of Selection */
    handleClick = () => {
      if (this.props.selectable) {
        this.props.onElementSelection(this.props.assetId, this.props.asset);
      }
    };

    updateSocketPos = (s) => {
      this.refs.socket.setZIndex(100);

      const coord = {
        x: s.target.attrs.x,
        y: s.target.attrs.y,
        inputConnections: [
          {
            x: this.state.image.width * 0.5,
            y:  this.state.image.height * 0.5,
          }
        ],
      };

      this.setState(coord);
      this.props.onPosChange(this.props.assetId, coord);
    }

    render() {

      let strokeColor = this.state.color;

      // Selected when either parent element (e.g. PDU outlet belongs to) is selected
      // or the socket was selected
      if (this.props.selectable) {
        strokeColor = (this.props.selected || this.props.parentSelected) ? "blue" : "grey";
      }

      return(
        <Group
          x={this.state.x}
          y={this.state.y}
          draggable={this.props.draggable}
          onDragMove={this.updateSocketPos.bind(this)}
          ref="socket"
        >
          {this.state.bgImage !== null &&
            <Image
              image={this.state.bgImage}
              stroke={strokeColor}
              onClick={this.handleClick}
            />

          }
          <Image
            image={this.state.image}
            stroke={strokeColor}
            onClick={this.handleClick}
          />

          {/* LED */}
          {this.props.selectable &&
            <SocketStatus socketOn={this.props.red_means_on?!this.props.asset.status:this.props.asset.status} powered={this.props.powered}/>
          }
          { !this.props.hideName &&
            <Text fontSize={14} fontFamily={'Helvetica'} text={this.props.asset && this.props.asset.name ? this.props.asset.name :'socket'}  y={this.state.bgImage ? 175: 105} />
          }
        </Group>
      );
    }
}

Socket.defaultProps = {
  red_means_on: false,
};

Socket.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  onPosChange: PropTypes.func.isRequired, // called on asset position change
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present
  draggable: PropTypes.bool, // Indicates if the outlet can be dragged
  red_means_on: PropTypes.bool, // For LED color: if it is red -> powered on
  asset: PropTypes.object, // Asset Details
  assetId: PropTypes.string, // Asset Key
  selected: PropTypes.bool, // Selected by user
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  onElementSelection: PropTypes.func, // Notify parent component of selection
  selectable: PropTypes.bool.isRequired, // Outlet is an asset,
  hideName: PropTypes.bool, // Display outlet name
};
