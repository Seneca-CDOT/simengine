import React from "react";
import PropTypes from "prop-types";
import { withStyles } from "@material-ui/core/styles";
import {
  Card,
  CardContent,
  CardHeader
  //   Divider,
  //   Typography
} from "@material-ui/core";
import { PlayArrow } from "@material-ui/icons";

// ** local imports
// import PowerSwitch from "./common/PowerSwitch";
import colors from "../styles/colors";

const Player = ({ classes }) => {
  return (
    <div>
      <Card className={classes.card}>
        <CardHeader
          title="Player"
          //   className={classes.cardHeader}
        />
        <CardContent>
          <PlayArrow />
        </CardContent>
      </Card>
    </div>
  );
};

Player.propTypes = {
  classes: PropTypes.object.isRequired
};

const styles = {
  card: {
    minWidth: 320,
    position: "absolute",
    bottom: 10,
    right: 20,
    boxShadow: "0 3em 14em rgba(0,0,0,.2)"
  },
  nestedElements: {
    maxHeight: 500,
    overflow: "auto"
  },
  cardHeader: {
    backgroundColor: "#e1e6ea"
  },
  statusOn: {
    color: colors.greenDark
  },
  statusOff: {
    colors: colors.grey
  },
  bullet: {
    display: "inline-block",
    margin: "0 2px",
    transform: "scale(0.8)"
  },
  title: {
    marginBottom: 16,
    fontSize: 14
  },
  pos: {
    marginBottom: 12
  }
};

export default withStyles(styles)(Player);
