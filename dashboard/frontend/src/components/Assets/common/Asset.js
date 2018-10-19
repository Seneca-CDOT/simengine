import React from 'react';
import PropTypes from 'prop-types';


/** 
 * Asset - aggregates some shared asset behaviour (selection & translation) 
 * */
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

  /** Load images into state (returns array of promises) */
  loadImages = (assetImages) => {
  
    let imagePromises = [];

    for (const [imageName, imageSource] of Object.entries(assetImages)) {
      
      if (!imageSource) { continue; }
      
      let image = new window.Image();
      image.src = imageSource;

      imagePromises.push(new Promise((resolve) => { 
        image.onload = () => { this.setState({ [imageName]: image }, () => resolve()); };
      }));
    }

    return imagePromises;
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