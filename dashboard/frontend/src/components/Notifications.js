
import React from 'react';
import Snackbar from '@material-ui/core/Snackbar';
import PropTypes from 'prop-types';


const Notifications = ({ anchorOrigin, displayedSnackbars }) => {

  const open = Object.keys(displayedSnackbars).find((k)=>displayedSnackbars[k]);

  let snackbarMessage = {};
  
  if (displayedSnackbars.socketOffline) {
    snackbarMessage = <span>Socket is unavailable: trying to reconnect...</span>;
  
  } else if (displayedSnackbars.changesSaved) {
    snackbarMessage = <span>Changes saved!</span>;

  } else if (displayedSnackbars.layoutEmpty) {
    snackbarMessage = (
      <span>
        The system toplology appears to be empty. <br/>
        Please, refer to the documentation (System Modelling
        <a href="https://simengine.readthedocs.io/en/latest/System%20Modeling/">link</a>)
      </span>
    );
  }

  return (
    <Snackbar
      anchorOrigin={anchorOrigin}
      open={open}
      message={<span>{snackbarMessage}</span>}
    />
  );
};

Notifications.propTypes = {
  anchorOrigin: PropTypes.object.isRequired, // notification position
  displayedSnackbars: PropTypes.object.isRequired, // indicates what snackbar message
};

export default Notifications;
