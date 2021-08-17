import React from 'react';
import LinearProgress from '@material-ui/core/LinearProgress';
import PropTypes from 'prop-types';

/**
 * Progress bar with background overlay
 */
const Progress = ({ completed }) => (
  <div className={completed < 100 ? 'progres-overlay' : ''}>
    <LinearProgress
      className="progress"
      variant="determinate"
      value={completed}
    />
  </div>
);

Progress.propTypes = {
  /** Percentage completed (0%-100%) */
  completed: PropTypes.number.isRequired,
};

export default Progress;
