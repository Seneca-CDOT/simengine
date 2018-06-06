import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';

const styles = {
  card: {
    minWidth: 275,
  },
  bullet: {
    display: 'inline-block',
    margin: '0 2px',
    transform: 'scale(0.8)',
  },
  title: {
    marginBottom: 16,
    fontSize: 14,
  },
  pos: {
    marginBottom: 12,
  },
};

function SimpleCard(props) {
  const { classes, elementInfo, assetId } = props;
  console.log(elementInfo)
  return (
    <div>
      <Card className={classes.card}>
        <CardContent>
          <Typography className={classes.title} color="textSecondary">
            Selected Asset
          </Typography>
          <Typography variant="headline" component="h2">
            Asset: {assetId}-{elementInfo[assetId].type}
          </Typography>
          <Typography component="p">
            The current status of the component is: {elementInfo[assetId].status}
          </Typography>
          {elementInfo[assetId].children && elementInfo[assetId].children.map(function(child, i){
            {console.log("child")}
            <div>

              <Typography variant="headline" component="h3">
                Nested Asset {i}: {child}-{elementInfo[child].type}
              </Typography>
              <Typography component="p">
                The current status of the component is: {elementInfo[assetId].status}
              </Typography>
            </div>
          })
          }
        </CardContent>
        <CardActions>
          <Button size="small">Learn More</Button>
        </CardActions>

      </Card>
    </div>
  );
}

SimpleCard.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SimpleCard);
