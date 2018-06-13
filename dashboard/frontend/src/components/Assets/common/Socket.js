
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import socket from '../../../images/socket.svg';
import SocketStatus from './SocketStatus';
import PropTypes from 'prop-types';


/**
 * Outlet Graphics
 */
export default class Socket extends React.Component {

    constructor() {
      super();
      this.state = {
        image: null,
        color: 'grey',
      };
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

     /** Notify Parent of Selection */
    handleClick = () => {
      if (this.props.selectable) {
        this.props.onElementSelection(this.props.assetId, this.props.asset);
      }
    };

    render() {

      let strokeColor = this.state.color;

      // Selected when either parent element (e.g. PDU outlet belongs to) is selected
      // or the socket was selected
      if (this.props.selectable) {
        strokeColor = (this.props.selected || this.props.parentSelected) ? "blue" : "grey";
      }

      return(
        <Group
          x={this.props.x?this.props.x:20}
        >
          <Image
            image={this.state.image}
            y={75}
            stroke={strokeColor}
            onClick={this.handleClick}
          />

          {/* LED */}
          {this.props.selectable &&
            <SocketStatus socketOn={this.props.asset.status}/>
          }
          <Text text={this.props.name ? this.props.name :'socket'}  y={180} />
        </Group>
      );
    }
}


Socket.propTypes = {
  name: PropTypes.string,
  x: PropTypes.number,
  asset: PropTypes.object, // Asset Details
  assetId: PropTypes.string, // Asset Key
  selected: PropTypes.bool, // Selected by user
  parentSelected: PropTypes.bool, // Used when an outlet belongs to an asset
  onElementSelection: PropTypes.func, // Notify parent component of selection
  selectable: PropTypes.bool.isRequired, // Outlet is an asset
};
