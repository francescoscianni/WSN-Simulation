from __future__ import annotations

import math
from dataclasses import dataclass
from random import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpy import Environment, Event

    from wsn_simulation.node import Node
    from wsn_simulation.message import Frame
    from wsn_simulation.manager import NetworkManager

import simpy.core


@dataclass
class MediaConfig:
    """
    Configuration for `Media`, representing wireless communication
    settings (media is the plural of the word medium).

    Hints for MobNet Students:
    - You probably don't need to touch this class :)
    - If you do not provide a default value, the field's value must be
        supplied on `Media` creation.
    - As a class constructor is generated from the fields below, it is
        important to list those without a default value before those
        which have a default.

    Attributes:
        env (simpy.Environment): The simulation environment in which
            the network operates, provided by SimPy.
        network (NetworkManager): The `NetworkManager` that
            coordinates network nodes and handles network-related
            operations.
        capacity (float): Maximum number of frames that the media
            channel can hold at once. Defaults to
            `simpy.core.Infinity`.
        base_loss_rate (float): Base probability of loss for a single
            transmission (0.0-1.0). Default is 0.6.
        DEBUG_MEDIA (bool): Enables debug logging for media events such
            as frame loss. Default is `False`.
        ENABLE_CI (bool): Enables constructive interference from
            identical transmissions.
    """

    env: Environment
    network: NetworkManager
    capacity: float = simpy.core.Infinity
    base_loss_rate: float = 0.6
    DEBUG_MEDIA: bool = False
    ENABLE_CI: bool = True


class Media:
    """
    Represents the wireless communication medium in the simulation
    (media is the plural of the word medium).

    This class models the behavior of a shared wireless channel,
    including constraints such as transmission range, channel matching,
    and frame loss due to fading.

    Hint for MobNet Students:
    - You probably don't need to touch this class :)

    Attributes:
        config (MediaConfig): Configuration object holding environment
            and network parameters.
        node_pipes (list): Stores communication channels for each node
            in the network, associating node IDs with SimPy `Store`
            objects.
    """

    def __init__(self, config: MediaConfig):
        """
        Initializes the `Media` object with simulation parameters.

        Parameters:
            config (MediaConfig): Contains environment, network
                manager, channel capacity, loss rate, and debug
                settings.
        """
        self.config: MediaConfig = config
        self.node_pipes: list[tuple[int, simpy.Store]] = []
        self._pending: list[Transmission] = []
        self._propagating: bool = False
        self._last_tx_time: dict[int, simpy.core.SimTime] = {}

    def get_output_conn(self, node_id: int) -> simpy.Store:
        """
        Provides a communication channel for a specified node.

        Creates and returns a new `Store` object for storing frames
        associated with the given node, and registers it in
        `node_pipes`.

        Parameters:
            node_id (int): The unique identifier of the node requiring
                the communication channel.

        Returns:
            simpy.Store: A storage object for handling frames for the
                node.
        """
        pipe = simpy.Store(self.config.env, capacity=self.config.capacity)
        self.node_pipes.append((node_id, pipe))
        return pipe

    def put(self, frame: Frame, transmitter_id: int) -> None:
        """
        Buffers all transmissions for the current slot and schedules
        processing.

        All transmissions within the same simulation tick are
        considered simultaneous.


        Parameters:
            frame: The frame to be transmitted, containing source and
                destination information.

        Raises:
            RuntimeError: If there are no available output pipes for
                transmission.
        """
        if not self.node_pipes:
            raise RuntimeError("There are no output pipes.")

        # only one message per transmitter allowed to be scheduled in a tick
        now = self.config.env.now
        if self._last_tx_time.get(transmitter_id) == now:
            return
        self._last_tx_time[transmitter_id] = now

        # schedule transmission from function argument
        self._pending.append(Transmission(frame, transmitter_id))
        if not self._propagating:
            # schedule an event to process pending transmissions
            self._propagation = self.config.env.event()
            self._propagation.callbacks.append(self._propagate)
            self._propagation._ok = True
            self.config.env.schedule(self._propagation)
            self._propagating = True

    def _propagate(self, event: Event) -> None:
        """
        Propagates buffered messages to nodes that meet the required
        conditions.

        Checks if each potential receiver node meets the following
        conditions:
        - Is within the sender's transmission range.
        - Is on the same communication channel as
        - Since devices are half-duplex, any incoming
            transmissions are dropped if device is transmitting.

        After processing transmissions, simulate constructive
        interference on the packets to determine whether the
        packet was lost.

        Parameters:
            event: this is a required input for event callbacks; not
                used.
        """
        rx_conditions = [self._in_range, self._on_channel]
        sender_ids = {tx.sender_id for tx in self._pending}
        # sweep receivers to check for incoming frames to process
        for receiver_id, store in self.node_pipes:
            rx: list[Transmission] = []
            if receiver_id in sender_ids:
                # half-duplex transmission: cannot tx and rx in one slot
                continue
            receiver = self.config.network.get_node(receiver_id)
            for tx in self._pending:
                sender = self.config.network.get_node(tx.sender_id)
                if all(c(sender, receiver) for c in rx_conditions):
                    # if the transmission passes range and channel filters...
                    rx.append(tx)
            # check filtered transmissions for loss
            rx = self._loss_handler(rx, receiver_id)
            for tx in rx:
                # put remaining transmissions in the receiver's simpy.Store
                store.put(tx.frame)

        # reset internal variables
        self._pending = []
        self._propagating = False

    def _loss_handler(
        self, transmissions: list[Transmission], receiver_id: int
    ) -> list[Transmission]:
        """
        Manages loss and collisions in the current slot.

        For the Glossy protocol, collisions can be constructive.
        This is an effect called "constructive interference" (CI).

        CI is handled by exponentially decreasing the static loss
        probability set in the `self.config.base_loss_rate` variable.

        CI is modelled such that the effective loss probability
        decreases sub-linearly with teh number of identical
        transmissions.

        The capture effect is NOT modelled. If multiple non-identical
        frames arrive, all are considered lost.

        Parameters:
            frames (list): All transmissions for a receiver in
                current tick
            receiver_id (int): For logging purposes
        Returns:
            frames (list): List of succesfully received (unique)
                transmissions.
        """
        if not transmissions:
            return []
        elif len(transmissions) == 1:
            # if only one transmission: static loss rate
            if random() < self.config.base_loss_rate:
                if self.config.DEBUG_MEDIA:
                    self.log(
                        f"DBG {transmissions[0].sender_id} -> "
                        f"{receiver_id} frame lost (fading)"
                    )
                return []
            else:
                return [transmissions[0]]
        elif self.config.ENABLE_CI:
            # if more than one transmission and with constructive interference
            senders = {tx.sender_id for tx in transmissions}

            # this should not happen since filtered in _propagate but...
            if receiver_id in senders:
                senders.remove(receiver_id)

            # extract frame identities (astulpe method of dataclass)
            identities = {tx.frame.identity for tx in transmissions}

            if len(identities) > 1:
                # destructive collisions if non-identical signals
                if self.config.DEBUG_MEDIA:
                    self.log(
                        f"DBG {senders} -> {receiver_id} frame(s) lost "
                        f"(collision of {len(identities)} distinct frames)"
                    )
                return []
            else:
                # constructive interference if identical signals
                k = len(transmissions)

                # effective loss rate decreases sublinearly wrt rx diversity
                effective_loss: float = (
                    self.config.base_loss_rate
                ) ** math.log2(k + 1)

                if random() < effective_loss:
                    return []
                else:
                    return [transmissions[0]]
        else:
            # destructive collisions
            return []

    def _in_range(self, sender: Node, receiver: Node) -> bool:
        """
        Determines if the receiver is within the sender's transmission
        range.

        Parameters:
            sender (Node): The node attempting to send the frame.
            receiver (Node): The potential receiving node.

        Returns:
            bool: `True` if the receiver is within the sender's range,
                `False` otherwise.
        """
        max_distance = sender.config.radio_txdistance
        distance = math.dist(sender.config.node_pos, receiver.config.node_pos)
        if distance > max_distance:
            # commented out out-of-range debug messages... for sanity:
            """
            if self.config.DEBUG_MEDIA:
                self.log(
                    f"DBG {sender.config.node_id} -> "
                    f"{receiver.config.node_id} frame lost (out-of-range)"
                )
            """
            return False
        return True

    def _on_channel(self, sender: Node, receiver: Node) -> bool:
        """
        Checks if the sender and receiver are on the same channel.

        Parameters:
            sender (Node): The node attempting to send the frame.
            receiver (Node): The potential receiving node.

        Returns:
            bool: `True` if both nodes share the same channel,
                `False` otherwise.
        """
        if receiver.config.radio_channel != sender.config.radio_channel:
            if self.config.DEBUG_MEDIA:
                self.log(
                    f"DBG {sender.config.node_id} -> "
                    f"{receiver.config.node_id} frame lost (wrong channel)"
                )
            return False
        return True

    def _not_lost(self, sender: Node, receiver: Node) -> bool:
        """
        Simulates signal fading to determine if a frame is lost.

        Parameters:
            sender (Node): The node attempting to send the frame.
            receiver (Node): The potential receiving node.

        Returns:
            bool: `True` if the frame is not lost, `False` otherwise.
        """
        if random() < float(self.config.base_loss_rate):
            if self.config.DEBUG_MEDIA:
                self.log(
                    f"DBG {sender.config.node_id} -> "
                    f"{receiver.config.node_id} frame lost (fading)"
                )
            return False
        return True

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
        timestamp = self.config.env.now / 1000
        node_name = self.__class__.__name__
        return f"[{timestamp:9.3f}  {node_name:<9}]"


@dataclass
class Transmission:
    """
    Represents a single on-air transmission event.

    This couples a Frame with the identity of the
    transmitting node. Transmitter identity is used by the medium
    to apply half-duplex constraints and collision rules.
    """

    frame: Frame
    sender_id: int
