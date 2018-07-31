const onWheelScroll = (stage) => {
  /////// Scale Layout on wheel event //////////
  stage.scale({ x: 0.7, y: 0.7 });
  stage.position({x: window.innerWidth * 0.3, y: window.innerHeight * 0.3 });

  const scaleBy = 1.03;
  window.addEventListener('wheel', (e) => {
    e.preventDefault();

    const oldScale = stage.scaleX();

    const mousePointTo = {
        x: stage.getPointerPosition().x / oldScale - stage.x() / oldScale,
        y: stage.getPointerPosition().y / oldScale - stage.y() / oldScale,
    };

    const newScale = e.deltaY > 0 ? oldScale * scaleBy : oldScale / scaleBy;
    stage.scale({ x: newScale, y: newScale });

    const newPos = {
        x: -(mousePointTo.x - stage.getPointerPosition().x / newScale) * newScale,
        y: -(mousePointTo.y - stage.getPointerPosition().y / newScale) * newScale
    };
    stage.position(newPos);
    stage.batchDraw();
  });
};

const onWheelDown = (stage) => {
  ////////// Move canvas on middle mouse button down ///////////
  const moveCanvas = (e) => {
    e.preventDefault();
      const newPos = {
        x: (stage.x() + e.movementX),
        y: (stage.y() + e.movementY),
    };
    stage.position(newPos);
    stage.batchDraw();
  };

  window.addEventListener("mousedown", (e) => {
    if (e.button == 1) {
      e.preventDefault();
      window.addEventListener("mousemove", moveCanvas);
    }
  });

  window.addEventListener("mouseup", (e) => {
    if (e.button == 1) {
      e.preventDefault();
      window.removeEventListener("mousemove", moveCanvas);
    }
  });
};

export { onWheelScroll, onWheelDown, };
