import React from 'react';
import { Group } from 'react-konva';
import PropTypes from 'prop-types';

/**
 * PointerElement cursor to pointer
 */
const PointerElement = ({ children }) => (
  <Group
    onMouseEnter={() => {
      document.body.style.cursor = 'pointer';
    }}
    onMouseLeave={() => {
      document.body.style.cursor = 'default';
    }}
  >
    {children}
  </Group>
);

PointerElement.propTypes = {
  /** children will have a mouse cursor set as a pointer*/
  children: PropTypes.node,
};

export default PointerElement;
