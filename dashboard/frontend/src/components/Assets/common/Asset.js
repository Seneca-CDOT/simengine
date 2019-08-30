import React from 'react';
import PropTypes from 'prop-types';

/**
 * Asset - aggregates some shared asset behaviour (selection & translation)
 * */
class Asset extends React.Component {
  loadImages = assetImages => {
    /** Load images into state (returns array of promises) */

    let imagePromises = [];

    for (const [imageName, imageSource] of Object.entries(assetImages)) {
      if (!imageSource) {
        continue;
      }

      let image = new window.Image();
      image.src = imageSource;

      imagePromises.push(
        new Promise(resolve => {
          image.onload = () => {
            this.setState({ [imageName]: image }, () => resolve());
          };
        }),
      );
    }

    return imagePromises;
  };

  // Asset position & IO coordinates //
  getOutputCoordinates = () => {
    return {};
  };
  getInputCoordinates = () => [];

  formatAssetCoordinates = ({ x, y }) => ({
    x: x, // asset position -> x
    y: y, // asset position -> y

    // i/o coordinates are relative to the asset { x, y } coordinates
    inputConnections: this.getInputCoordinates(), // input power position { x, y }
    outputConnections: this.getOutputCoordinates(), // output power position { x, y } (if supported)
  });

  /** Notify Parent of Selection */
  handleClick = () => {
    this.refs.asset.setZIndex(100);
    this.props.onElementSelection(this.props.asset);
  };

  /** returns global asset position (x, y), relative output & input outlet coordinates */
  updateAssetPos = s => {
    const coord = this.formatAssetCoordinates(s.target.attrs);
    this.props.onPosChange(this.props.asset.key, coord);
  };
}

Asset.defaultProps = { x: 0, y: 0, powered: false, isComponent: false };

Asset.propTypes = {
  /** X position of the asset */
  x: PropTypes.number,
  /** Y position of the asset */
  y: PropTypes.number,
  /** font size of the label */
  fontSize: PropTypes.number,
  /** asset setails (status, key etc.) */
  asset: PropTypes.object.isRequired,
  /** indicates if asset is currently selected */
  selected: PropTypes.bool.isRequired,
  /** indicates if upstream power is present */
  powered: PropTypes.bool.isRequired,
  /** called upon asset translation */
  onPosChange: PropTypes.func.isRequired,
  /** notify parent component of asset selection */
  onElementSelection: PropTypes.func.isRequired,
};

export default Asset;
