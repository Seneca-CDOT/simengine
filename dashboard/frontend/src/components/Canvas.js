import React, { Component } from 'react';
// import PropTypes from 'prop-types';
import { Stage, Layer, Line } from 'react-konva';

import { onWheelScroll, onWheelDown } from './canvasEvents';


class Canvas extends Component {

  componentDidMount() {
    let stage = this.refs.stage.getStage();
    // scale on wheel scroll, and move canvas on middle button click
    onWheelScroll(stage);
    onWheelDown(stage);
  }


  render() {
    return (
      <Stage
        width={window.innerWidth}
        height={window.innerHeight * 0.88}
        ref="stage"
      >
        <Layer>
          {systemLayout}
          {wireDrawing}
        </Layer>
      </Stage>
    );
  }
}

Canvas.propTypes = {

};

export default Canvas;
