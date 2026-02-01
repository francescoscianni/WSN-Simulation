from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

import simpy

from wsn_simulation.manager import NetworkManager
from wsn_simulation.media import Media, MediaConfig
from wsn_simulation.node import NodeConfig
from wsn_simulation.node.sensor import Sensor
from wsn_simulation.node.sink import Sink
from wsn_simulation.results import get_results


def main(
    *,
    debug_mode: bool = False,
    max_transmissions: int = 1,
    loss_rate: float = 0.6,
    max_hops: int = 4,
    guard_time: int = 100,
    rng_seed: int | None = None,
) -> tuple[Any, ...]:
    """
    The main entry point for the simulation.

    This function sets up the simulation environment, initializes the
    network manager, creates the media for communication, adds nodes
    to the simulation, and runs the simulation for a specified
    duration.

    The simulation environment is managed by `simpy.Environment`, and
    it includes network nodes that communicate through the media
    object.

    The simulation runs until all scheduled events in simpy's event
    queue are processed.
    The nodes will perform their actions during this time based on
    the logic defined in their respective processes.

    This function is the primary programmatic API of the simulator
    and is intended to be called repeatedly (e.g., for Monte Carlo
    experiments).


    Steps performed in this function:
    1. Initializes the random number generator with a timestamp seed.
    2. Sets up the SimPy environment for the simulation.
    3. Creates a `NetworkManager` to manage the nodes in the network.
    4. Initializes the communication medium (wireless channel) used
        by the nodes.
    5. Calls the `add_nodes()` function to add nodes (e.g., `Sensor`,
        `Sink`) to the network.
    6. Runs the simulation until all events are processed.

    Notes:
    - The `add_nodes()` function is responsible for placing nodes
        at specific positions in the simulation space.
    - The simulation environment handles the timing of events and
        processes in the network.

    Returns:
        SimulationResults (tuple): Result fields are
        placeholders in the baseline implementation and are
        expected to be populated by protocol logic implemented
        by students in the node subpackage.

    """

    validate_simulation_parameters(
        max_transmissions=max_transmissions,
        loss_rate=loss_rate,
        max_hops=max_hops,
        guard_time=guard_time,
    )
    # Initialization of the random generator
    if debug_mode:
        rng_seed = 0
        random.seed(0)
    elif rng_seed is not None:
        random.seed(rng_seed)
    else:
        random.seed()

    # Setup of the simulation environment
    env = simpy.Environment()

    # Create the network manager for a shared medium
    network_manager = NetworkManager()

    # Generate the medium for the communication
    media = Media(
        MediaConfig(
            env=env,
            network=network_manager,
            base_loss_rate=loss_rate,
            DEBUG_MEDIA=debug_mode,
        )
    )

    # Add nodes to the simulation
    add_nodes(
        env=env,
        network=network_manager,
        media=media,
        max_transmissions=max_transmissions,
        max_hops=max_hops,
        guard_time=guard_time,
        debug_mode=debug_mode,
    )

    # Execute the experiment
    env.run()

    results = get_results(
        max_transmissions=max_transmissions,
        max_hops=max_hops,
        seed=rng_seed,
        loss_rate=loss_rate,
        debug_mode=debug_mode,
        manager=network_manager,
    )

    return results.as_tuple


def add_nodes(
    env: simpy.Environment,
    network: NetworkManager,
    media: Media,
    max_transmissions: int,
    max_hops: int,
    guard_time: int,
    debug_mode: bool = False,
) -> None:
    """
    Creates a layered grid topology and adds all nodes to the
    network.

    Nodes are placed on integer coordinates in a square grid
    centered at (0, 0). The hop of a node is defined as the
    Chebyshev distance (max(|x|, |y|)) from the sink.

    Node IDs are assigned layer by layer, starting from the sink
    (hop 0) and increasing outward.

    The sink node is placed at (0, 0) and assigned node_id = 1.
    All other nodes are instantiated as sensor nodes.

    Parameters:
        env (simpy.Environment): Simulation environment
        network (NetworkManager): Network manager instance
        media (Media): Shared communication medium
        max_transmissions (int): The maximum number of transmissions
            a node performs in one single flood
        max_hops (int): Maximum hop distance from the sink
        debug (bool): Whether to change the default debug values in
            the NodeConfig definition
    """

    hops: dict[int, list[tuple[int, int]]] = {}

    for y in range(-max_hops, max_hops + 1):
        for x in range(-max_hops, max_hops + 1):
            hop = max(abs(x), abs(y))
            hops.setdefault(hop, []).append((x, y))

    node_id = 1
    for hop in range(max_hops + 1):
        for x, y in sorted(hops[hop]):
            network.add_node(
                Sink(
                    env,
                    media,
                    NodeConfig(
                        node_id,
                        x,
                        y,
                        node_hop=hop,
                        max_transmissions=max_transmissions,
                        guard_time=guard_time,
                        DEBUG_POSITION=debug_mode,
                        DEBUG_RADIO=debug_mode,
                        DEBUG_SENSOR=debug_mode,
                    ),
                )
                if x == 0 and y == 0
                else Sensor(
                    env,
                    media,
                    NodeConfig(
                        node_id,
                        x,
                        y,
                        node_hop=hop,
                        max_transmissions=max_transmissions,
                        guard_time=guard_time,
                        DEBUG_POSITION=debug_mode,
                        DEBUG_RADIO=debug_mode,
                        DEBUG_SENSOR=debug_mode,
                    ),
                )
            )
            node_id += 1


def validate_simulation_parameters(
    *,
    max_transmissions: int,
    loss_rate: float,
    max_hops: int,
    guard_time: int,
) -> None:
    """
    Validate user- and program-supplied simulation parameters.
    """
    if max_transmissions < 0:
        raise ValueError(
            "transmission count must be positive integer greater or equal to 0"
        )
    if loss_rate < 0.0 or loss_rate > 1.0:
        raise ValueError(
            "loss rate must be positive float smaller or equal to 1.0"
        )
    if max_hops < 1:
        raise ValueError(
            "hop count must be a positive integer greater or equal to 1"
        )
    if guard_time < 1:
        raise ValueError(
            "guard time must be positive integer greater or equal to 1"
        )
