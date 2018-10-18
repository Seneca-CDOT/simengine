import React from 'react';
import { Path } from 'react-konva';
import PropTypes from 'prop-types';

import colors from '../../../styles/colors';

/**
 * AssetOutline (.svg outline of the asset)
 */
const AssetOutline = ({ path, selected, onClick }) => {

    return (
        <Path data={path}
          strokeWidth={0.4}
          stroke={selected ? colors.selectedAsset : colors.deselectedAsset}
          fill={colors.backgroundAssetColor}
          scale={{x: 4, y: 4}}
          y={-575}
          onClick={onClick}
        />
    );
};

AssetOutline.propTypes = {
  path: PropTypes.string.isRequired, // .svg path
  onClick: PropTypes.func.isRequired, // Y position of the asset
  selected: PropTypes.bool.React, // indicates if the asset is selected
};

export default AssetOutline;
