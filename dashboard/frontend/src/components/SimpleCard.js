import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import CardHeader from '@material-ui/core/CardHeader';
import Divider from '@material-ui/core/Divider';
import Typography from '@material-ui/core/Typography';
import Switch from '@material-ui/core/Switch';
import FormControlLabel from '@material-ui/core/FormControlLabel';

const styles = {
  card: {
    minWidth: 320,
    position: 'absolute',
    top: 90,
    right: 20,
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
  const { classes, elementInfo, assetId, changeStatus, showHeader=true } = props;
  let children = [];

  if(elementInfo[assetId].children) {
    children.push(
      <div>
      <h3>
        Connected Components
      </h3>
      </div>
    );
    for (let child of elementInfo[assetId].children){
        children.push(
        <div key={child}>
            <Typography variant="subheading" component="h5">
              Nested Asset: {child}-{elementInfo[child].type}
            </Typography>
                <Typography component="p">
                  ::Status-{elementInfo[child].status === 1?<span style={{color: 'green'}}>on</span>:<span style={{color: 'red'}}>off</span>}
                </Typography>
          </div>
        );
    }
  }

  return (
    <div>
      <Card className={classes.card}>
        {showHeader &&
          <CardHeader
            title="Selected Asset Details"
            style={{ backgroundColor: '#e1e6ea' }}
          />
        }
        <CardContent>
          <Typography variant="headline" component="h2">
            Asset: {assetId}-{elementInfo[assetId].type}
          </Typography>
          <Typography component="p">
            Status: {elementInfo[assetId].status === 1?<span style={{color: 'green'}}>on</span>:<span style={{color: 'red'}}>off</span>}
          </Typography>
          <Divider />
            <FormControlLabel
              control={<Switch checked={elementInfo[assetId].status} aria-label="LoginSwitch" onChange={()=>changeStatus(assetId)}/>}
              label={"Toggle Status"}
            />
          <Divider/>
          {children}
        </CardContent>
        {/*
        <CardActions>
          <Button size="small">Learn More</Button>
        </CardActions>
        */}
      </Card>
    </div>
  );
}

SimpleCard.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SimpleCard);
