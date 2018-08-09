
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import socket from '../../../images/socket.svg';
import SocketStatus from './SocketStatus';
import PropTypes from 'prop-types';


/**
 * Outlet Graphics
 */
export default class Socket extends React.Component {

    constructor(props) {
      super();
      this.state = {
        image: null,
        color: 'grey',
        x: props.x?props.x:40,
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

    componentWillReceiveProps(newProps) {
      this.setState({ x: newProps.x, y: newProps.y });
    }

     /** Notify Parent of Selection */
    handleClick = () => {
      if (this.props.selectable) {
        this.props.onElementSelection(this.props.assetId, this.props.asset);
      }
    };

    updateSocketPos = (s) => {
      this.refs.socket.setZIndex(100);
      this.setState({ x: s.target.attrs.x, y : s.target.attrs.y });
      this.props.onPosChange(this.props.assetId, s);
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
  red_means_on: true,
};

Socket.propTypes = {
  x: PropTypes.number,
  asset: PropTypes.object, // Asset Details
  assetId: PropTypes.string, // Asset Key
  selected: PropTypes.bool, // Selected by user
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  onElementSelection: PropTypes.func, // Notify parent component of selection
  selectable: PropTypes.bool.isRequired, // Outlet is an asset,
  hideName: PropTypes.bool, // Display outlet name
};
