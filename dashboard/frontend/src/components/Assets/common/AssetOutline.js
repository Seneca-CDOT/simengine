import React, { Fragment } from 'react';
import { Path } from 'react-konva';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * AssetOutline (.svg outline of the asset)
 */
const AssetOutline = ({ path, selected, onClick, scale, children }) => (
  <Fragment>
    <Path data={path}
      fill={colors.backgroundAssetColor}
      scale={scale}
      y={-575} 
    />
    {children}
    <Path data={path}
      strokeWidth={0.4}
      stroke={selected ? colors.selectedAsset : colors.deselectedAsset}
      fill={null}
      scale={scale}
      y={-575 /*?!...*/} 
      onClick={onClick}
    />
  </Fragment>
);

AssetOutline.defaultProps = {
  scale: {x: 4, y: 4,}
};

AssetOutline.propTypes = {
  /** svg path */
  path: PropTypes.string.isRequired,
  /** on path selection */
  onClick: PropTypes.func,
  /** indicates if the asset is selected */
  selected: PropTypes.bool.isRequired,
  /** scale of the path */
  scale: PropTypes.object.isRequired,
  /** components to be encosed in the asset outline (non-selectable items) */
  children: PropTypes.object,
};

export default AssetOutline;
