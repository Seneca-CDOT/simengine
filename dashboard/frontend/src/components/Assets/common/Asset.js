import React from 'react';
import PropTypes from 'prop-types';

class Asset extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      x: props.x,
      y: props.y,
    };
  }

  componentWillReceiveProps(newProps) {
    this.setState({ x: newProps.x, y: newProps.y });
  }

  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.asset.setZIndex(100);
    this.props.onElementSelection(this.props.assetId, this.props.asset);
  };

  getOutputCoordinates = () => {}
  getInputCoordinates = () => []

  /** returns global asset position (x, y), relative output & input outlet coordinates */
  updateAssetPos = (s) => {
    const coord = {
      x: s.target.attrs.x,
      y: s.target.attrs.y,
      inputConnections: this.getInputCoordinates(),
      outputConnections: this.getOutputCoordinates(),
    };

    this.setState(coord);
    this.props.onPosChange(this.props.assetId, coord);
  }

}

Asset.propTypes = {
  x: PropTypes.number, // X position of the asset
  y: PropTypes.number, // Y position of the asset
  asset: PropTypes.object.isRequired, // Asset Details
  assetId: PropTypes.string.isRequired, // Asset Key
  
  selected: PropTypes.bool.isRequired, // Asset Selected by a user
  powered: PropTypes.bool.isRequired, // indicates if upstream power is present

  onPosChange: PropTypes.func.isRequired, // called on Asset position change
  onElementSelection: PropTypes.func.isRequired, // Notify parent component of selection
};


export default Asset;