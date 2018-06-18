import React from 'react';
import { Rect } from 'react-konva';

/**
 * LED of a socket
 */
export default class SocketStatus extends React.Component {

  render() {
    const color = this.props.socketOn?"green": "red";
    return (
      <Rect
        x={this.props.x?this.props.x:20}
        y={85}
        width={10}
        height={10}
        fill={color}
        shadowBlur={5}
        onClick={this.handleClick}

        />
    )}
}
