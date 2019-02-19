
import React from 'react';
import LinearProgress from '@material-ui/core/LinearProgress';
import PropTypes from 'prop-types';


const Progress = ({ completed }) => {

  return (
    <div className={completed<100?'progres-overlay':''}>
      <LinearProgress className="progress" variant="determinate" value={completed} />
    </div>
  );
};

Progress.propTypes = {
  completed: PropTypes.number.isRequired, // notification position
};

export default Progress;
