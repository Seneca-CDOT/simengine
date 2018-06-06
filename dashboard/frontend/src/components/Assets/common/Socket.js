
import React from 'react';
import { Text, Image, Group } from 'react-konva';
import socket from '../../../images/socket.svg';
import SocketStatus from './SocketStatus';

export default class Socket extends React.Component {

    constructor() {
      super();
      this.state = {
        image: null,
        color: 'grey',
        selected: false,
      };

      this.myRef = React.createRef();
    }

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

    handleClick = () => {

      if (this.props.selectable) {
        const selected = !this.state.selected;
        const color = selected ? 'blue':'grey';

        this.setState({
          color,
          selected: selected
        });

        if(selected) {
          this.props.onElementSelection(this.props.elementId);
        }
      }
    };

    render() {
      return(
        <Group
          x={this.props.x?this.props.x:20} ref={this.myRef}
        >
          <Image
            image={this.state.image}
            y={75}
            stroke={this.state.color}
            onClick={this.handleClick}
          />
          {this.props.selectable &&
            <SocketStatus/>
          }
          <Text text={this.props.socketName ?this.props.socketName:'socket'}  y={180} />
        </Group>
      );
    }
}
