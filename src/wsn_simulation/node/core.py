from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpy import Environment
    from simpy.core import SimTime

    from wsn_simulation.media import Media
    from wsn_simulation.message import Message

from wsn_simulation.message import FloodBeaconMessage, Frame


@dataclass
class NodeConfig:
    """
    Dataclass to define simulation configuration parameters for each
    node.

    This class holds configuration data for nodes in the simulation.
    These parameters are required to define the node's characteristics,
    such as its position, radio range, and debugging options.

    If you do not provide a default value, the field's value must be
    supplied on node creation.

    As a class constructor is generated from the fields below, it
    is important to list those without a default value before those
    which have a default.

    Hints for MobNet Students:
    - This is the initial configuration for each node. You can add
        fields below if you need to.

    Attributes:
        node_id (int): The unique identifier for the node.
        node_posx (int): The x-coordinate position of the node.
        node_posy (int): The y-coordinate position of the node.
        node_hop (int): The hop distance to the sink, derived from
            the network topology (e.g., grid layer).
        max_transmissions (int): The maximum number of transmissions
            a node performs during one flood.
        guard_time (SimTime): The guard time (in ms) between consecutive
            slots in Glossy
        radio_txdistance (int): The transmission range of the node
            (default is 1.5).
        radio_channel (int): The transmission channel selected for the
            node (default is 7).
        DEBUG_POSITION (bool): Flag whether to print a message
            indicating a created node's position.
        DEBUG_RADIO (bool): Flag to enable/disable radio debugging
            (default is False).
        node_pos (tuple[int, int]): A tuple of the node's x and y
            coordinates.
    """

    node_id: int  # the id of the node
    node_posx: int  # the x axis position of the node
    node_posy: int  # the y axis position of the node
    node_hop: int  # the hop distance to the sink
    max_transmissions: int = 1  # the number of transmissions in one flood
    guard_time: SimTime = 50.0  # ms of guard time between slots
    radio_txdistance: float = 1.5  # transmission range of nodes
    radio_channel: int = 7  # selected transmission channel
    DEBUG_POSITION: bool = False  # whether to print node position messages
    DEBUG_RADIO: bool = False  # debug messages for the low level radio
    DEBUG_SENSOR: bool = True  # debug messages for physical sensors

    @property
    def node_pos(self):
        """
        Returns the position of the node as a tuple of (x, y)
        coordinates.

        Returns:
            tuple[int, int]: The (x, y) position of the node.
        """
        return (self.node_posx, self.node_posy)


class Node:
    """
    A base node class providing basic sensing and communication
    functionality.

    This class defines an underlying node object, from which specific
    node types like `Sensor` and `Sink` can inherit. It includes
    methods for sending and receiving messages, managing node state,
    and logging.

    Hints for MobNet Students:
    - This class defines an underlying object for the nodes. This means
    that anything you add here will be present in the Sink and Sensor
    objects.

    Attributes:
        env (Environment): The simulation environment that manages the
            event queue.
        config (NodeConfig): The configuration settings for the node.
        media_in (Media): The media through which the node receives
            messages.
        media_out (Media): The media through which the node sends
            messages.
    """

    def __init__(
        self, env: Environment, media: Media, config: NodeConfig
    ) -> None:
        """
        Initializes the node with the given environment, media, and
        configuration.

        **Hint for MobNet Students**:
        - A class' __init__ method is called only once, when the object
            is created!

        Parameters:
            env (Environment): The simulation environment.
            media (Media): The communication media for the node.
            config (NodeConfig): The configuration object for the node.
        """
        self.env = env
        self.config = config
        self.media_in = media.get_output_conn(self.config.node_id)
        self.media_out = media
        self.flood_beacon_ids: set[str] = set()
        self.flood_beacon_times: dict[str, set[SimTime]] = {}
        self.local_tx_count: int = 0
        self.radio_rx_enable: bool = True

    def generate_frame(
        self,
        msg_type: str,
        src_id: int,
        dst_id: int,
        msg_seq: int,
        payload: Message,
    ) -> Frame:
        """
        Generates a message frame to be sent to another node.

        This method packages the data and creates a frame that
        include the source node ID, destination node ID,
        sequence number, and message payload.

        The generated frame represents an on-air packet.
        Transmitter identity is handled by the medium and is not
        part of the frame.

        The frame is treated as an immutable on-air packet and must
        not be modified by intermediate nodes.


        Parameters:
            msg_type (str): The type of message being sent.
            src_id (int): The message source node ID.
            dst_id (int): The message destination node ID.
                This is the logical destination.
                A value of 0 represents a network-layer
                broadcast.
            msg_seq (int): The message sequence number.
                This value is provided by the protocol logic
                (e.g., Sink). The node does not generate or
                modify the sequence numbers.
            payload (Message): The message content (payload).

        Returns:
            Frame: A `Frame` object representing the message to be
                sent.
        """
        return Frame(
            TYPE=msg_type,
            SRC=src_id,
            DST=dst_id,
            SEQ=msg_seq,
            PAYLOAD=payload,
        )

    def set_channel(self, new_channel: int) -> None:
        """
        Sets the communication channel of the node.

        Parameters:
            new_channel (int): The new channel to be set_.

        Returns:
            None
        """
        self.config.radio_channel = new_channel

    def sleep(self, duration: SimTime):
        """
        Makes the node sleep for the specified duration in 'ticks' of
        the simulation (representing milliseconds).

        This method returns a generator that can be yielded in the
        simulation's event loop.

        Parameters:
            duration (int): The duration (in time units) the node
              should sleep.

        Returns:
            Timeout: A generator that yields the sleep event in the
              simulation.
        """
        return self.env.timeout(duration)

    def send(self, frame: Frame) -> None:
        """
        Sends a message frame through the media.

        This method puts the frame onto the media, making it
        available for other nodes to receive.

        Note 1: Transmissions are assumed to have zero duration and
        are resolved by the medium at the end of the current
        simulation tick.

        Note 2: If multiple nodes call send() within the same
        simulation tick, the medium resolves their interaction
        jointly (collision / CI).

        This method also increments the global transmission counter
        used for experimental evaluation.

        Parameters:
            frame (Frame): The frame to be sent to other nodes.
        """
        if not self.radio_rx_enable:
            return
        self.radio_rx_enable = False
        self.local_tx_count += 1
        if self.config.DEBUG_RADIO:
            self.log(f"DBG {self.config.node_id} -> {frame.DST}")
        self.media_out.put(frame, self.config.node_id)

        def reenable_rx():
            yield self.sleep(self.config.guard_time)
            self.radio_rx_enable = True

        self.env.process(reenable_rx())

    def receive(self, frame: Frame) -> Frame | None:
        """
        Processes a received message frame.

        This baseline implementation performs only destination
        filtering.

        It does NOT implement:
        - duplicate suppression
        - retransmission
        - protocol-specific logic

        Protocol behavior (e.g., flooding, retransmission) must be
        implemented in subclasses.

        IMPORTANT:
        - Reception of FLOOD_BEACON messages is automatically recorded
        by the framework when a FloodBeaconMessage reaches this method.
        - Students MUST NOT manually record reception statistics.
        - A node is considered to have received a flood if a
        FloodBeaconMessage is passed to this method.

        Parameters:
            frame (Frame): The frame that was received.

        Returns:
            The method returns the frame as a `Frame` object if the
            frame is valid for this node. If the frame is not valid,
            the method returns `None`.
        """
        if not self.radio_rx_enable:
            if self.config.DEBUG_RADIO:
                self.log("DBG discard frame (radio busy with tx)")
            return None
        if (frame.DST != 0) and (frame.DST != self.config.node_id):
            if self.config.DEBUG_RADIO:
                self.log("DBG discard frame (not logical destination)")
            return None
        if frame.TYPE == "FLOOD_BEACON" and isinstance(
            frame.PAYLOAD, FloodBeaconMessage
        ):
            self._record_flood_beacons(frame.PAYLOAD)
        return frame

    def _record_flood_beacons(self, payload: FloodBeaconMessage) -> None:
        """
        Records the reception of a flood beacon payload.

        This method tracks both the identity of the flood instance
        and the simulation times at which the beacon was received.
        Multiple receptions of the same flood beacon are recorded
        to allow analysis of retransmissions and synchronization
        behavior.

        Protocol logic must not invoke this method directly.
        """
        flood_id = payload.FLOOD_ID
        flood_time = self.env.now
        self.flood_beacon_ids.add(payload.FLOOD_ID)
        self.flood_beacon_times.setdefault(flood_id, set()).add(flood_time)

    def log(self, msg: str) -> None:
        """
        Outputs a debug message with a standardized format.

        This method prepends a timestamp and class name prefix to the
        provided message and then prints it to the console.

        Parameters:
            msg (str): The message to be logged.

        Returns:
            None: The formatted message is printed directly to
                the console.
        """
        print(f"{self.log_prefix}  {msg}")

    @property
    def log_prefix(self) -> str:
        """
        Generates a standardized log prefix with timestamp and class
        name.

        Returns:
            str: A formatted prefix containing the current timestamp
                and the class name for each log entry.
        """
        timestamp = self.env.now / 1000
        node_name = self.__class__.__name__
        node_id = self.config.node_id
        hop = self.config.node_hop
        return f"[{timestamp:9.3f}  {node_name:<6}  {node_id:<1d} (hop {hop})]"
