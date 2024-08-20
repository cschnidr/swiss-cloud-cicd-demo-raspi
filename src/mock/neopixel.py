import logging

RGB = "RGB"
GRB = "GRB"

class NeoPixel():
  def __init__(
        self,
        pin: None,
        n: int,
        *,
        bpp: int = 3,
        brightness: float = 1.0,
        auto_write: bool = True,
        pixel_order: str = None
    ):
    logging.info("NeoPixel MOCK init")

  def deinit(self) -> None:
    logging.info("NeoPixel MOCK deinit")

  def show(self) -> None:
    logging.debug("NeoPixel MOCK show")