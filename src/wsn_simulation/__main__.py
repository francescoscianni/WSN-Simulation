#######################################################################
#                                                                     #
#                                                                     #
#                           wsn-simulation                            #
#                                                                     #
#                                                                     #
#######################################################################
"""

This simulator was developed by Prof. Utz Roedig at the University
College Cork [1]. It was repackaged for the Mobile Networks course of
Prof. Matthias Hollick at the Technical University of Darmstadt [2].

LICENSE: please contact Prof. Roedig [1] for authorization to reuse
this code.

 [1]    Prof. Utz Roedig.
         School of Computer Science and Information Technology.
         University College Cork.
         URL: https://research.ucc.ie/profiles/D005/u.roedig@ucc.ie
 [2]    Prof. Matthias Hollick.
         Department of Computer Science.
         Technical University of Darmstadt.
         URL: https://www.seemoo.tu-darmstadt.de/team/mhollick/

"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

from argparse import ArgumentParser

from wsn_simulation.core import main, validate_simulation_parameters


def parse_args_() -> dict[str, Any]:
    """
    Parses command-line arguments for the simulation.

    This interface is intended to support batch experiments
    (e.g., Monte Carlo runs) by varying topology size, loss
    rate, and random seed.


    To see available arguments, use the "-h" argument

    Returns:
        debug (bool): Whether to activate the debug mode.
        max_transmissions (int): Number of retransmissions a node
            performs after first reception of a flood message.
        loss_rate (float): The loss probability for a single packet
            transmission.
        max_hops (int): The maximum hop distance from the sink in
            the grid topology.
        guard_time (int): The guard time in simulation ticks between
            consecutive frame retransmissions.
        seed (int | None): The seed for random. If none provided, a
            non-deterministic is used.
    """
    parser = ArgumentParser(
        prog="simulate",
        description="A simpy-based WSN simulator "
        "used as part of the bonus system of the "
        "Mobile Networks course of the Technical "
        "University of Darmstadt",
    )
    parser.add_argument(
        "-d",
        "--debug-mode",
        action="store_true",
        default=False,
        help="Enables debug mode. This: "
        "1. seeds the PRNG with 0 (simulation becomes repeatable); "
        "2. flips all debug flags to true. "
        "Default: %(default)s",
    )
    parser.add_argument(
        "-t",
        "--max-transmissions",
        type=int,
        default=1,
        required=False,
        help="(int) Number of retransmissions a node performs after first "
        "reception of a flood message. "
        "Must be >= 0 | "
        "Effect depends on node retransmission logic implemented in Task 1 | "
        "Default: %(default)s",
    )
    parser.add_argument(
        "-l",
        "--loss-rate",
        type=float,
        default=0.6,
        required=False,
        help="(float) Loss rate for a single packet transmission. "
        "Must be between 0.0 and 1.0 | "
        "Default: %(default)s",
    )
    parser.add_argument(
        "-m",
        "--max-hops",
        type=int,
        default=4,
        required=False,
        help="(int) The maximum hop distance (Chebyshev distance) from the "
        "sink in the grid topology. "
        "Must be >= 1 | "
        "Default: %(default)s",
    )
    parser.add_argument(
        "-g",
        "--guard-time",
        type=int,
        default=100,
        required=False,
        help="(int) Guard time in simulation ticks between consecutive "
        "retransmissions. "
        "Must be >= 1 | "
        "Used by node retransmission logic implemented in Task 1 | "
        "Default: %(default)s",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=None,
        required=False,
        help="(int) Random seed for the simulation. "
        "If omitted, a non-deterministic seed is used | "
        "Default: %(default)s",
    )
    args = parser.parse_args()
    validate_simulation_parameters(
        max_transmissions=args.max_transmissions,
        loss_rate=args.loss_rate,
        max_hops=args.max_hops,
        guard_time=args.guard_time,
    )
    return {
        "debug_mode": args.debug_mode,
        "max_transmissions": args.max_transmissions,
        "loss_rate": args.loss_rate,
        "max_hops": args.max_hops,
        "guard_time": args.guard_time,
        "rng_seed": args.seed,
    }


def run() -> None:
    main(**parse_args_())


if __name__ == "__main__":
    run()
