from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpy import Environment

    from wsn_simulation.media import Media
    from wsn_simulation.node.core import NodeConfig

from wsn_simulation.message import Frame,Message,FloodBeaconMessage, frame_to_json
from wsn_simulation.node.core import Node



class Sensor(Node):
    """
    A Sensor node in the wireless sensor network simulation.

    The `Sensor` node simulates a sensor device.

    In the baseline implementation, the sensor does not generate
    data. All protocol behavior is to be implemented by
    students.

    **Hints for MobNet students**:
    - This class defines the `Sensor` node.
    - If you want to modify how `Sensor` nodes behave, this is the file
        to edit.
    """
    
    def __init__(
        self, env: Environment, media: Media, config: NodeConfig
    ) -> None:
        """
        Initializes a new `Sensor` node.

        This method sets up the sensor by calling the parent `Node`
        class' constructor, logs the creation of the sensor node, and
        starts one main process:
        1. `__receive_process()` for receiving incoming messages.

        Parameters:
            env (Environment): The simulation environment that the
                `Sensor` node operates within.
            media (Media): The medium through which the `Sensor`
                communicates.
            config (NodeConfig): The configuration object that defines
                the sensor's settings such as its ID, position, etc.
        """
        # This calls __init__ of the Node class (cf. node.py)
        super().__init__(env, media, config)
        if self.config.DEBUG_POSITION:
            self.log(
                f"    new sensor node ({self.config.node_posx}|"
                f"{self.config.node_posy})"
            )
        self.env.process(self._receive_process())
        

    def _receive_process(self):
        """
        The receive process of the `Sensor` node, responsible for
        waiting for and processing incoming frames.

        This method listens for any frames that are sent to this
        node. When a frame is received, it checks whether the
        message should be processed and logs the reception of the
        message.
        """
        while True:
            # Waits until the incoming media sees a frame
            frame: Frame = yield self.media_in.get()
            flood_id = frame.PAYLOAD.FLOOD_ID
            is_new = flood_id not in self.flood_beacon_ids
            # If a message has actually been received, process it:
            if self.receive(frame) is not None:
                # remove logging in your monte carlo runs for a little speed:
                self.log(f"<-  receiving {frame_to_json(frame)}")
                if frame.TYPE == "FLOOD_BEACON" and is_new:
                    self.env.process(self._flood_process(frame))
                    
   
    def _flood_process(self, frame: Frame):
        for i in range(self.config.max_transmissions):
            yield self.sleep(self.config.guard_time)
            self.send(frame)
                    
                    
                
                
                
