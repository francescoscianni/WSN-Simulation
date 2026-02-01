from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpy import Environment

    from wsn_simulation.media import Media
    from wsn_simulation.node.core import NodeConfig

from wsn_simulation.message import FloodBeaconMessage, frame_to_json, Frame
from wsn_simulation.node.core import Node


class Sink(Node):
    """
    A Sink node in the wireless sensor network simulation.

    The `Sink` node represents a node that receives and processes
    frames sent by other nodes in the network. It continuously
    listens for incoming frames, processes them, and can perform
    actions based on the contents of those frames.

    Note: This baseline Sink implementation only initiates a single
    flood. It does not implement repeated rounds, acknowledgments,
    or termination.
    These behaviors are left to students.

    Hints for MobNet students:
    - This class defines the baseline `Sink` implementation.
    - The baseline only initiates a single flood by transmitting
    a message of type "FLOOD_BEACON".
    - It does not implement repeated rounds.
    - If you need to modify how only `Sink` nodes behave, you
        should edit this class.

    """

    def __init__(
        self, env: Environment, media: Media, config: NodeConfig
    ) -> None:
        """
        Initializes the Sink node with its environment, media, and
        configuration.

        Hints for MobNet students:
        - This method initializes the `Sink` by calling the parent
            class' (`Node`) constructor, logging the creation of the
            `Sink`, and starting two main processes:
        1. `__main_process()` to simulate the `Sink` node's activities;
        2. `__receive_process()` to handle incoming frames.
        - The msg_seq is only controlled by the protocol (i.e., the
        `Sink` maintains the flood variable and iterates at the
        start of every flood).

        Parameters:
            env (Environment): The simulation environment in which the
                `Sink` operates.
            media (Media): The media through which the `Sink`
                communicates with other nodes.
            config (NodeConfig): The configuration object containing
                the node's settings.
        """
        super().__init__(env, media, config)
        if self.config.DEBUG_POSITION:
            self.log(
                f"    new sink node ({self.config.node_posx}|"
                f"{self.config.node_posy})"
            )
        self.env.process(self._main_process())
        self.env.process(self._receive_process())
        self.msg_seq = -1

    def _main_process(self):
        """
        This method is responsible for simulating the core activity
        of the `Sink` node. Can be extended to implement additional
        behaviors specific to `Sink` nodes.

        As a baseline, it waits 100 ms and then triggers a flood by
        broadcasting a "FLOOD_BEACON"-type message.
        """
        # Wait 100ms before sending the flood beacon frame
        yield self.sleep(100)
        self.trigger_flood()

    def _receive_process(self):
        """
        The receive process of the `Sink` node, responsible for
        handling incoming frames.

        This method listens for incoming messages (frames) through
        the media connection. When a frame is received, the `Sink`
        will attempt to process it. If a frame is successfully
        received, it is logged and can be acted upon (e.g., stored,
        analyzed).
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

    def trigger_flood(self):
        """
        Initiates a single flood round by incrementing the flood
        sequence number and broadcasting a FLOOD_BEACON packet.

        The flood beacon carries a unique flood identifier that
        remains constant across retransmissions.
        """

        # Iterates the sequence number
        self.increment_sequence_number()

        # Generate a flood beacon id
        flood_id = uuid.uuid4().hex

        # Record the flood_id as seen
        self.flood_beacon_ids.add(flood_id)
        time = self.env.now
        self.flood_beacon_times.setdefault(flood_id, set()).add(time)

        # Send a frame object
        # Here, it is a broadcast on network layer (DST = 0)
        frame = self.generate_frame(
            msg_type="FLOOD_BEACON",
            src_id=self.config.node_id,
            dst_id=0,
            msg_seq=self.msg_seq,
            payload=FloodBeaconMessage(FLOOD_ID=flood_id),
        )
        self.send(frame)
        self.env.process(self._flood_process(frame))

    def increment_sequence_number(self) -> None:
        """
        Increments the message sequence number.

        This method is used to ensure that each message sent has a
        unique sequence number.
        This sequence number identifies the flood epoch.

        Returns:
            None
        """
        self.msg_seq += 1
