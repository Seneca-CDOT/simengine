/** Scale Layout on wheel event */
const onWheelScroll = (stage) => {
  stage.scale({ x: 0.7, y: 0.7 });
  stage.position({ x: window.innerWidth * 0.3, y: window.innerHeight * 0.3 });

  const scaleBy = 1.03;
  window.addEventListener('wheel', (e) => {
    const oldScale = stage.scaleX();

    if (!stage.getPointerPosition()) {
      return;
    }

    const mousePointTo = {
      x: stage.getPointerPosition().x / oldScale - stage.x() / oldScale,
      y: stage.getPointerPosition().y / oldScale - stage.y() / oldScale,
    };

    const newScale = e.deltaY > 0 ? oldScale * scaleBy : oldScale / scaleBy;
    stage.scale({ x: newScale, y: newScale });

    const newPos = {
      x: -(mousePointTo.x - stage.getPointerPosition().x / newScale) * newScale,
      y: -(mousePointTo.y - stage.getPointerPosition().y / newScale) * newScale,
    };
    stage.position(newPos);
    stage.batchDraw();
  });
};

/** Move canvas on middle mouse button down */
const onWheelDown = (stage) => {
  const moveCanvas = (e) => {
    const newPos = {
      x: stage.x() + e.movementX,
      y: stage.y() + e.movementY,
    };
    stage.position(newPos);
    stage.batchDraw();
  };

  window.addEventListener('mousedown', (e) => {
    if (e.button == 1) {
      window.addEventListener('mousemove', moveCanvas);
    }
  });

  window.addEventListener('mouseup', (e) => {
    if (e.button == 1) {
      window.removeEventListener('mousemove', moveCanvas);
    }
  });
};

/** Resize canvas/stage on window changes */
const fitStageIntoParent = (stage) => {
  const fitStage = () => {
    stage.width(window.innerWidth);
    stage.height(window.innerHeight * 0.99);
    stage.batchDraw();
  };

  fitStage();
  window.addEventListener('resize', fitStage);
};

export { onWheelScroll, onWheelDown, fitStageIntoParent };
