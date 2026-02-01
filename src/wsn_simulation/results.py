from __future__ import annotations

from dataclasses import astuple, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from wsn_simulation.manager import NetworkManager


@dataclass(frozen=True)
class SimulationResults:
    """
    Container for aggregated simulation results.

    This dataclass represents the outcome of a single simulation run.
    It collects high-level metrics derived from the final network
    state and protocol execution, such as flood coverage, completion
    time, and total transmission count.

    Instances of this class are intended to be used for:
    - batch experiments
    - Monte Carlo simulations
    - statistical analysis
    - export to CSV / NumPy / pandas

    All fields are immutable to ensure reproducibility and to prevent
    accidental modification of recorded results.

    Attributes:
        max_transmissions (int):
            The maximum number of transmissions each node performs
            in one flooding round.
        loss_rate (float):
            Base loss probability of a single transmission.
        guard_time (float):
            The guard time between slots in Glossy
        seed (int | None):
            Random seed used for the simulation, if any.
        max_hops (int):
            Maximum hop distance of the grid topology.
        device_count (int):
            The number of devices (Sensors and Sink).
        flood_success (bool):
            True if all nodes received the flood at least once.
        flood_coverage (float):
            Fraction of nodes that received the flood.
        completion_time (float):
            Simulation time at which the last node first received
            the flood (in simulation time units - ms).
        total_transmissions (int):
            Total number of transmissions in the network.
    """

    max_transmissions: int
    loss_rate: float
    guard_time: float
    seed: int | None
    max_hops: int
    device_count: int
    flood_success: bool
    flood_coverage: float
    completion_time: float
    total_transmissions: int

    @property
    def as_tuple(self) -> tuple[Any, ...]:
        """
        Returns the simulation results as a tuple.

        This representation is convenient for batch processing,
        logging, and exporting results to external tools such as
        CSV files, NumPy arrays, or pandas DataFrames.

        The order of elements corresponds to the field order of
        the SimulationResults dataclass.
        """
        return astuple(self)


def get_results(
    max_transmissions: int,
    loss_rate: float,
    seed: int | None,
    max_hops: int,
    debug_mode: bool,
    manager: NetworkManager,
) -> SimulationResults:
    """
    Extracts and aggregates simulation results from the final
    network state.

    This function is called after the simulation has completed.
    It inspects the network manager and associated nodes to
    compute high-level metrics describing the outcome of the
    flooding protocol.

    Importantly, this function must not influence protocol
    behavior or simulation timing. It is purely observational
    and serves as the boundary between protocol execution and
    experimental evaluation.

    Parameters:
        max_transmissions (int):
            The maximum number of transmissions each node performs
            in one flooding round.
        loss_rate (float):
            Base loss probability configured for the medium.
        seed (int | None):
            Random seed used for the simulation run.
        max_hops (int):
            Maximum hop distance used to construct the network
            topology.
        manager (NetworkManager):
            Network manager containing all nodes and their
            final state.

    Returns:
        SimulationResults:
            An immutable summary of the simulation outcome.
    """
    nodes = manager.nodes
    total_nodes = len(nodes)
    guard_time = float(nodes[0].config.guard_time)

    received_nodes = [node for node in nodes if node.flood_beacon_ids]

    flood_coverage = (
        len(received_nodes) / total_nodes if total_nodes > 0 else 0.0
    )
    flood_success = flood_coverage == 1.0

    completion_time: float = 0.0
    if flood_success:
        first_rx_times: list[float] = []
        for node in received_nodes:
            for times in node.flood_beacon_times.values():
                if times:
                    first_rx_times.append(float(min(times)))

        completion_time = max(first_rx_times) if first_rx_times else 0.0

    total_transmissions = sum(node.local_tx_count for node in manager.nodes)

    if debug_mode:
        print("*** DEBUG MODE ACTIVE ***")
        print("Run results:")
        print(f"max_transmissions: {max_transmissions}")
        print(f"loss_rate: {loss_rate}")
        print(f"guard_time: {guard_time}")
        print(f"seed: {seed}")
        print(f"max_hops: {max_hops}")
        print(f"device_count: {total_nodes}")
        print(f"flood_coverage: {flood_coverage}")
        print(f"flood_success: {flood_success}")
        print(f"completion_time: {completion_time}")
        print(f"total_transmissions: {total_transmissions}")

    return SimulationResults(
        max_transmissions=max_transmissions,
        loss_rate=loss_rate,
        guard_time=guard_time,
        seed=seed,
        max_hops=max_hops,
        device_count=total_nodes,
        flood_coverage=flood_coverage,
        flood_success=flood_success,
        completion_time=completion_time,
        total_transmissions=total_transmissions,
    )
