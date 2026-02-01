from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wsn_simulation.node import Node


class NetworkManager:
    """
    A `NetworkManager` class to manage a collection of network nodes.

    This class represents a network that maintains a list of nodes,
    each uniquely identified by a `node_id`. It provides methods to
    add, remove, and retrieve nodes, as well as track the total count
    of nodes in the network.

    The NetworkManager does not implement routing or protocol logic.
    It only provides node lookup and bookkeeping.

    Hint for MobNet Students:
    - You probably don't need to touch this class :)

    Methods:
        - add_node(node: Node) -> None: Adds a new node to the network.
        - remove_node(node: Node) -> None: Removes a node from the
                network.
        - get_node(node_id: int) -> Node: Retrieves a node by its ID.
    """

    def __init__(self):
        """
        Initializes an empty network with a list to store nodes and
        a `node_count` attribute set to zero.

        The `node_count` tracks the number of nodes currently in the
        network.

        The `DEBUG_NETWORK` flag flips the DEBUG flags in each node
        and in the media to `True`.
        """
        self.nodes: list[Node] = []
        self._node_by_id: dict[int, Node] = {}
        self.node_count = 0

    def _update_node_count(self) -> None:
        """
        Private method to update the `node_count` attribute based on
        the current number of nodes in the network.

        This method is called after any node is added or removed from
        the network to ensure the `node_count` is accurate.
        """
        self.node_count = len(self.nodes)

    def add_node(self, node: Node) -> None:
        """
        Adds a new, unique `Node` to the network.

        The method checks if the node already exists in the network
        by either the node object or its `node_id`. If a node with
        the same ID or the same object already exists, a `ValueError`
        is raised.

        Parameters:
            node (Node): The `Node` object to be added to the network.

        Raises:
            ValueError: If a node with the same `node_id` or the same
                        object is already present in the network.
        """
        node_id = node.config.node_id
        if node_id in self._node_by_id:
            raise ValueError(f"node_id {node_id} already in use")
        self.nodes.append(node)
        self._node_by_id[node_id] = node
        self._update_node_count()

    def remove_node(self, node: Node) -> None:
        """
        Removes the specified `Node` from the network.

        This method attempts to remove the node from the list of nodes.
        If the node is not found, a `ValueError` is raised.

        Parameters:
            node (Node): The `Node` object to be removed from the
                network.

        Raises:
            ValueError: If the node is not found in the network.
        """
        node_id = node.config.node_id
        try:
            self.nodes.remove(node)
            del self._node_by_id[node_id]
        except (ValueError, KeyError):
            raise ValueError(f"Node {node_id} not found in network.")
        self._update_node_count()

    def get_node(self, node_id: int) -> Node:
        """
        Retrieves a `Node` by its unique `node_id` from the network.

        This method searches the network for a node with the given
        `node_id`. If no matching node is found, a `ValueError` is
        raised.

        Parameters:
            node_id (int): The unique identifier of the node to
                retrieve.

        Returns:
            Node: The `Node` object with the matching `node_id`.

        Raises:
            ValueError: If no node with the given `node_id` is found.
        """
        try:
            return self._node_by_id[node_id]
        except KeyError:
            raise ValueError(f"node_id {node_id} not found in the network")
