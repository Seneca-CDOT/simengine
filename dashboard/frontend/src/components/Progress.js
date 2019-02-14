
import React from 'react';
import LinearProgress from '@material-ui/core/LinearProgress';
import PropTypes from 'prop-types';


const Progress = ({ completed }) => {


  return (
    <div>
        <LinearProgress variant="determinate" value={completed} />
    </div>
  );
};

Progress.propTypes = {
  anchorOrigin: PropTypes.object.isRequired, // notification position
  displayedSnackbars: PropTypes.object.isRequired, // indicates what snackbar message
};

export default Progress;
