import React from 'react';
import { Path } from 'react-konva';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * AssetOutline (.svg outline of the asset)
 */
const AssetOutline = ({ path, selected, onClick, scale }) => (
  <Path data={path}
    strokeWidth={0.4}
    stroke={selected ? colors.selectedAsset : colors.deselectedAsset}
    fill={colors.backgroundAssetColor}
    scale={scale}
    y={-575 /*?!...*/} 
    onClick={onClick}
  />
);

AssetOutline.defaultProps = {
  scale: {x: 4, y: 4,}
};

AssetOutline.propTypes = {
  path: PropTypes.string.isRequired, // .svg path
  onClick: PropTypes.func.isRequired, // Y position of the asset
  selected: PropTypes.bool.isRequired, // indicates if the asset is selected
  scale: PropTypes.object.isRequired,
};

export default AssetOutline;
