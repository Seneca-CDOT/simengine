import React from 'react';
import { Rect } from 'react-konva';

export default class SocketStatus extends React.Component {

  state = {
    color: 'red'
  };

  handleClick = () => {
    this.setState({
      color: "green"
    });
  };

  render() {
    const color = this.props.socketOn?"green": "red";
    return (
      <Rect
        x={this.props.x?this.props.x:20}
        y={150}
        width={10}
        height={10}
        fill={color}
        shadowBlur={5}
        onClick={this.handleClick}

        />
    )}
}
