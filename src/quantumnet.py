"""
CSC 4501 Computer Networks
QuantumNet: Routing and Congestion in a Distributed Quantum Network

STUDENT STARTER FILE

No prior quantum-computing knowledge is required. In this project:
- QPUs are network nodes.
- Quantum links are graph edges.
- An entanglement request is treated as an end-to-end network request.
- The focus is routing, reliability, capacity, queueing, congestion, and throughput.

Complete the TODO sections. Do not rename required functions unless instructed.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


@dataclass
class Request:
    request_id: int
    arrival_ms: float
    src: str
    dst: str


@dataclass
class RequestResult:
    request_id: int
    policy: str
    src: str
    dst: str
    arrival_ms: float
    finish_ms: float
    latency_ms: float
    waiting_ms: float
    hop_count: int
    success: bool
    path: str


# ============================================================
# TASK 1 — Build and validate the network topology [10 points]
# ============================================================

def load_topology(path: str | Path) -> nx.Graph:
    """
    Read data/topology.json and return an undirected NetworkX graph.

    Required checks:
      1. 0 < success_prob <= 1
      2. capacity >= 1
      3. the graph is connected
    """

    G = nx.Graph()

    # read the JSON file
    with open(path) as f:
        topology = json.load(f)

    # add all nodes
    for node in topology['nodes']:
            G.add_node(node)

    # add all links
    for link in topology['links']:
        G.add_edge(
            link['u'],
            link['v'],
            de = link['delay_ms'],
            pe = link['success_prob'],
            ce = link['capacity']
        )

    # validate success_prob (pe)
    for u, v, pe in G.edges.data('pe'):                                             # https://networkx.org/documentation/stable/reference/introduction.html#graph-reporting
        if not(0 < pe and pe <= 1):
            print("invalid success probability:", pe, "for link", u, ",", v)
            print("valid probability values are between 0 and 1")
            print()

    # validate link capacity (ce)
    for u, v, ce in G.edges.data('ce'):
        if not(ce >= 1):
            print("invalid link capacity:", ce, "for link", u, ",", v)
            print("valid link capacities are greater than 1")
            print()

    # validate that the graph is connected
    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.is_connected.html#networkx.algorithms.components.is_connected
    
        # "A graph is connected if, for every pair of distinct nodes,
        # there is a path between them. If there is a pair of nodes
        # for which such path does not exist, the graph is not connected
        # (also referred to as “disconnected”)"
        
    validate_connected = nx.is_connected(G)
    
    if validate_connected == True:
        print("graph is connected")
        print()
    else:
        print("graph is NOT connected")
        print()
            
    return G

    # TODO 1:

    # - Read the JSON file.
    # - Add all nodes.
    # - Add all links with delay_ms, success_prob, and capacity.
    # - Validate the link values and graph connectivity.
    raise NotImplementedError("Complete Task 1")


def draw_topology(g: nx.Graph, output_path: str | Path) -> None:
    """Provided visualization helper. You may improve the layout if desired."""
    pos = {
        "Q1": (0.0, 1.0),
        "Q2": (2.0, 1.8),
        "Q3": (2.0, 0.2),
        "Q4": (4.2, 1.8),
        "Q5": (4.2, 0.2),
        "Q6": (6.2, 1.0),
    }

    ordered_edges = [
        ("Q1", "Q2"), ("Q1", "Q3"), ("Q2", "Q3"),
        ("Q2", "Q4"), ("Q3", "Q4"), ("Q3", "Q5"),
        ("Q4", "Q5"), ("Q4", "Q6"), ("Q5", "Q6"),
    ]
    labels = {edge: f"L{i}" for i, edge in enumerate(ordered_edges, start=1)}

    plt.figure(figsize=(8.4, 3.7))
    nx.draw_networkx_nodes(g, pos=pos, node_size=1050)
    nx.draw_networkx_edges(g, pos=pos, width=1.4)
    nx.draw_networkx_labels(g, pos=pos, font_size=10)
    nx.draw_networkx_edge_labels(
        g, pos=pos, edge_labels=labels, font_size=8, rotate=False
    )
    plt.title("Six-QPU Distributed Network Topology")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close()

# graph = load_topology('../data/topology.json')                  # this also happens in main
# draw_topology(graph, '../outputs/topology.png')               # why can't I get permission to write to /student/outputs????
# draw_topology(graph, '../topology.png')

# graph is not connected
#test_graph = load_topology('../data/topology_test.json')
#draw_topology(test_graph, '../topology_test.png')

# ============================================================
# TASK 2 — Generate network traffic [10 points]
# ============================================================

def generate_requests(
    g: nx.Graph,
    n_requests: int,
    arrival_rate_per_ms: float,
    rng: random.Random,
) -> List[Request]:
    """
    Generate requests using exponentially distributed inter-arrival times.

    Hint:
        rng.expovariate(arrival_rate_per_ms)

    Every request needs:
        request_id, arrival_ms, src, dst

    Source and destination must be different.
    """

    requests = []                                                   # function expects a list to be returned, "requests" is that list

    id = 0
    arrival_ms = 0                                                  # time the request arrives

    while id < n_requests:
        # two non-repeating random samples from g.nodes
        srcdst = rng.sample(list(g.nodes), k = 2)
        arrival_ms += rng.expovariate(arrival_rate_per_ms)          # requests are generated in order of arrival time so arrival time increments with each request

        requests.append(
            Request(
                request_id = id,
                arrival_ms = arrival_ms,
                src = srcdst[0],
                dst = srcdst[1]
            )
        )
        id = id +1
    return requests

    # TODO 2
    raise NotImplementedError("Complete Task 2")


# ============================================================
# TASK 3 — Implement routing policies [30 points]
# ============================================================

# determines how a given edge gets its weight depending on which policy is passed as the arg
# dijkstra's algorithm finds the path with the LOWEST total accumulated weight

def edge_weight(
    policy: str,
    attrs: dict,
    alpha: float = 1.0,
    beta: float = 15.0,
) -> float:
    """
    Required policies:

    shortest_hop:
        Minimum number of links.

    min_latency:
        Minimum total delay.

    max_reliability:
        Maximum product of link success probabilities.
        Convert this into an additive Dijkstra edge cost.

    student_policy:
        Your own policy using at least TWO link properties.
        Explain the formula and parameters in your report.
    """

    delay = attrs["de"]                                 # delay = attrs["delay_ms"]
    p = attrs["pe"]                                     # p = attrs["success_prob"]
    capacity = attrs["ce"]                              # capacity = attrs["capacity"]

    if policy == "shortest_hop":
        # TODO 3A

        # every link has weight of 1
        # dijkstra's algorithm chooses the path with the least amount of links

        return 1

        raise NotImplementedError("Complete Task 3A")

    if policy == "min_latency":
        # TODO 3B

        # every link's weight is its (the link's) delay (de)
        # dijkstra's algorithm chooses the path with the least amount of overall delay

        return delay                                        # delay = "delay", line 247

        raise NotImplementedError("Complete Task 3B")

    if policy == "max_reliability":
        # TODO 3C

        # dijkstra's algorithm computes a sum,
        # however the most reliable path = highest pe * pe * pe ... * pe

        # Hint: logarithms convert products into sums.
        # i.e., log(a * b) = log(a) + log(b)
        # but we want high success probability to be represented by a SMALLER number,
        # try: -(log(a) + log(b)).
        # But how do we do this on a per weight basis? distribute the -:
        # (-log(a)) + (-log(b))

        return -math.log(p)                                 # probability = "p", line 248

        raise NotImplementedError("Complete Task 3C")

    if policy == "student_policy":
        # TODO 3D
        # Use at least TWO of: delay, p, capacity.

        # if there's high capacity and low delay,
        # we can send a lot of data with minimal delay
        # and brute force our way through low success probability

        # higher capacities --> lower quotients for (1/capacity)
        # higher delays --> contribute more to (delay + (1/capacity)) 

        return delay + (1/capacity)

        # for this policy we expect more losses than other policies,
        # but for successful tranmissions, faster delivery
        # of the *entire* payload, not just one segment
 
        raise NotImplementedError("Complete Task 3D")

    raise ValueError(f"Unknown policy: {policy}")


def choose_path(
    g: nx.Graph,
    src: str,
    dst: str,
    policy: str,
    alpha: float = 1.0,
    beta: float = 15.0,
) -> List[str]:

    """Select a path using Dijkstra's algorithm and edge_weight(...)."""
    # TODO 3E

    def weight_func(src, dst, attrs):                               # the weight of a given link is the result of...
        return edge_weight(policy, attrs, alpha, beta)              # calling edge_weight w/given args

    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.dijkstra_path.html#dijkstra-path
    path = nx.dijkstra_path(g, src, dst, weight=weight_func)
    # weight_func() means call the function now, without supplying the required arguments
    # weight_func means pass the function itself to NetworkX
    #       - NetworkX will call weight_func(src, dst, attrs) as it examines each edge

    return path

    raise NotImplementedError("Complete Task 3E")


# ============================================================
# TASK 4 — Model link capacity and queueing [15 points]
# ============================================================

class LinkState:
    """
    A link has a finite number of simultaneous service slots.

    Recommended representation:
        store one next-available time per slot in a min-heap.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity                                                # Each link has ce simultaneous service slots.

        # TODO 4A:
        # Create a min-heap with one 0.0 value per capacity slot.

        self.available_times = []

        i = 0
        while i < capacity:                                                     # loop adds one 0.0 value per capacity slot
            self.available_times.append(0.0)
            i = i + 1

        # Min-heaps are binary trees for which every parent node has a value less than or equal to any of its children.
        # https://docs.python.org/3/library/heapq.html

        heapq.heapify(self.available_times)                                     # Create a min-heap

        self.busy_time = 0.0                                                    # total time link was in use
        self.jobs = 0                                                           # total number of times link was used 

    def reserve(self, ready_ms: float, service_ms: float) -> Tuple[float, float]:
        """
        Return (start_time, finish_time).

        start_time = max(ready_ms, earliest_slot_free_time)
        finish_time = start_time + service_ms
        """
        # TODO 4B:
        # Update the slot heap, busy_time, and jobs.

        self.jobs = self.jobs + 1                                               # because we just accepted a job
        self.busy_time = self.busy_time + service_ms                            # because we're keeping track of total time the link was in use

        earliest_slot_free_time = heapq.heappop(self.available_times)           # because this job took the shortest time-until-available value

        start_time = max(ready_ms, earliest_slot_free_time)                     # the job cannot start until the link available and the job is ready, so of the two, whichever time is longer will be the job's start time
        finish_time = start_time + service_ms                                   # this job's finish time is it's start time + the time it takes to complete this job

        heapq.heappush(self.available_times, finish_time)                       # theres one element per service slot
        #                                                                       # add this jobs finish time to that array so when something comes looking for a service slot, it can accuratly choose the soonest one

        reservation = (start_time, finish_time)

        return reservation
        raise NotImplementedError("Complete Task 4B")


def canonical_edge(u: str, v: str) -> Tuple[str, str]:
    return tuple(sorted((u, v)))


def make_link_states(g: nx.Graph) -> Dict[Tuple[str, str], LinkState]:
    """Create one LinkState object for each network link."""
    # TODO 4C

    # for every edge in the graph get it's capacity so we can create a linkstate object
    # for every link pair it with the subsequent linkstate object and store that pair in link_states

    # canonical edge gives a single pair for every combination of two nodes that are attached to a link
    # so we don't have two entries in link_states for a single link

    linkstate_objects = {}

    for u, v in g.edges:
        linkstate_objects[canonical_edge(u, v)] = LinkState(g.edges[u, v]["ce"])                                # edge lookup is G.edges[u, v] (https://networkx.org/documentation/stable/reference/introduction.html#graph-reporting)

    return linkstate_objects
    raise NotImplementedError("Complete Task 4C")


# ============================================================
# TASK 5 — End-to-end simulation and metrics [20 points]
# ============================================================

def simulate(
    g: nx.Graph,
    requests: List[Request],
    policy: str,
    seed: int,
    alpha: float = 1.0,
    beta: float = 15.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    For each request:
      1. choose a route;
      2. traverse links in path order;
      3. reserve link capacity;
      4. accumulate queue waiting time;
      5. sample link success/failure;
      6. stop after the first failed link;
      7. record the result.

    A link succeeds when:
        rng.random() <= success_prob
    """
    # TODO 5A:
    # Initialize random generator and link states.

    generator = random.Random(seed)
    linkstate_objects = make_link_states(g)

    # TODO 5B:
    # Process requests in increasing arrival-time order.

    # requests are generated in order of arrival time
    # just to be safe, sort them in ascending order of arrival time anyway:
    
    # selection sort
    for i in range(len(requests)):
        for j in range(i + 1, len(requests)):
            if requests[j].arrival_ms < requests[i].arrival_ms:
                requests[i], requests[j] = requests[j], requests[i]

    # ========================================================================================================================================
    request_results = []
    link_results = []
    # ========================================================================================================================================
    
    for request in requests:
        request_success = 0                                                                 # if the request is successful, this will be changed to 1
        request_arrival = request.arrival_ms                                                # get the value of the arrival time of the request
        request_id = request.request_id
        request_src = request.src
        request_dst = request.dst
    
        request_wait = 0                                                                    # sum of waiting at each link = total wait time for this request
        request_hops = 0
        request_latency = None                                                              # latency is the time it takes for data to get from point A to point B, if the data makes it to point B this is changed to the difference between the finish time of the last hop and the arrival time

        #hop_finish_times = []                                                               # list of finish times for each hop in the request
        hop_finish = 0

        # ========================================================================================================================================
        path = choose_path(g, request.src, request.dst, policy, alpha, beta)                # returns a list of nodes in the path
        # ========================================================================================================================================

        i = 1                                                                               # links in the path --> link i = 1 through link i = len(path) - 1
        while i < len(path):                                                                # link i = len(path) - 1 will be the last iteration in the while loop
            u = path[i -1]                                                                  # the start node for the current (local) hop
            v = path[i]                                                                     # the desintain node for the current (local) hop

            link = linkstate_objects[canonical_edge(u, v)]                                  # so we can call reserve on the linkstate_object for this link and get the start time and finish time of this hop

            # .reserve needs ready_ms and service_ms
            #       - service_ms == value stored for this link's delay (de)
            service_ms = g.edges[u, v]["de"]
            #       - ready_ms depends on if there was a previous hop
            #               - if there was a previous hop, ready_ms = finish_time of previous hop
            #               - if there was no previous hop, ready_ms = arrival time of the request
            if i == 1:
                ready_ms = request.arrival_ms                                               # no previous hop
            else:
                ready_ms = finish_time                                                      # there is a previous hop
            
            start_time, finish_time = link.reserve(ready_ms, service_ms)
            #hop_finish_times.append(finish_time)                                                # add the finish time to the list of finish times
            hop_finish = finish_time

            # now the we know the ready time and the actual start time, we can calculate the time spent waiting by finding the difference between the two times
            link_wait = start_time - ready_ms
            # update the total time spend waiting for this request
            request_wait = request_wait + link_wait

            # ========================================================================================================================================

            # now that we know the ready time, time spent waiting, and the estimated finish time, actually attempt the hop

            if generator.random() <= g.edges[u, v]["pe"]:                                   # if this condition is met the hop was successful

                request_hops = request_hops + 1                                             # increment the total number of successful hop counts for this request

                if i == (len(path) - 1):                                                    # if the hop was successful and i == (len(path) - 1), we made the final hop in the path
                    request_success = 1                                                     # meaning the whole request was successful
                    #last_successful_hop_finish = finish_time                                # the finish time of the last successful hop is this hop's finish time
                    request_latency = finish_time - request_arrival                         # latency is the time it takes for data to get from point A to point B, if the request was successful then that means latency == last finish time (finish time for this iteration) - arrival time
                
                i = i + 1                                                                   # move to the next hop

            else:                                                                           # if random.random() > g.edges[u, v]["success_prob"], the hop was not successful (the link is "failed")
                #last_successful_hop_finish = hop_finish_times[len(hop_finish_times) - 2]    # the finish time of the last successful hop was the previous hop (a successful hop)'s finish time
                i = len(path)                                                               # ends the while loop, since we stop after the first failed link

        # ========================================================================================================================================
        request_results.append({
            "request_id": request_id,
            "policy": policy,
            "src": request_src,
            "dst": request_dst,
            "arrival_ms": request_arrival,                                                  # the arrival time of this request
            "finish_ms": hop_finish,                                                        # formerly the finish time of the last successful hop for this request, now the finish time of the last attempted hop (regardless if it was successful or a failure)
            "latency_ms": request_latency,
            "waiting_ms": request_wait,                                                     # total time spend waiting for this request
            "hop_count": request_hops,                                                      # number of successful hops for this request
            "success": request_success,                                                     # if this request succeeded
            "path": path
        })

    # ========================================================================================================================================

    request_df = pd.DataFrame(request_results)

    simulation_time = request_df["finish_ms"].agg("max") - request_df["arrival_ms"].agg("min")

    # ========================================================================================================================================

    # once all the requests are done, create link_df which stores stats per-link

    for link in linkstate_objects:
        linkstate_obj = linkstate_objects[link]

        link_results.append({
            "policy": policy,
            "link": link,
            "jobs": linkstate_obj.jobs,
            "utilization": (linkstate_obj.busy_time / (linkstate_obj.capacity * simulation_time))
        })

    link_df = pd.DataFrame(link_results)

    # ========================================================================================================================================

    # TODO 5C:
    # Return:
    #   request_df with per-request results
    #   link_df with policy, link, jobs, utilization

    #request_df = pd.DataFrame(request_results)
    #link_df = pd.DataFrame(link_results)

    return (request_df,link_df)

    raise NotImplementedError("Complete Task 5")


def summarize(request_df: pd.DataFrame, offered_load: float) -> dict:
    """
    Compute:
      policy
      offered_load
      success_rate
      avg_latency_ms
      avg_waiting_ms
      avg_hops
      throughput_req_per_s
    """
    # =============================================================================
    request_summary = []

    policy = request_df["policy"].iloc[0]                                                                           # all requests in a single simulation use the same policy
    num_successful_requests = request_df["success"].agg("sum")                                                      # success = 1 if successful, so sum on the success column = num of successful requests

    # ============================ SUCCESS RATE ===================================
    num_requests = request_df["success"].agg("count")                                                               # counts number of rows in request_df, which == number of requests
    request_success_rate = (num_successful_requests / num_requests) * 100

    # ============================ AVG LATENCY ====================================
    avg_latency = request_df["latency_ms"].agg("mean")

    # ============================ AVG WAIT TIME ==================================
    avg_wait_time = request_df["waiting_ms"].agg("mean")

    # ============================ AVG HOPS =======================================
    avg_hops = request_df["hop_count"].agg("mean")

    # ============================ THROUGHPUT =====================================
    simulation_time = request_df["finish_ms"].agg("max") - request_df["arrival_ms"].agg("min")            # simulation time = (max last-successful-hop's finish time) - (min arrival time)
    throughput = (num_successful_requests / simulation_time) * 1000                                       # simulation time is in ms, to get requests per second multiply by 1000

    # =============================================================================
    request_summary.append({
        "policy": policy,
        "offered_load": offered_load,
        "success_rate": request_success_rate,
        "avg_latency_ms": avg_latency,
        "avg_waiting_ms": avg_wait_time,
        "avg_hops": avg_hops,
        "throughput_req_per_s": throughput
    })

    return request_summary
    # =============================================================================

    # TODO 5D
    raise NotImplementedError("Complete Task 5D")


# ============================================================
# TASK 6 — Experimental evaluation and report [15 points]
# ============================================================

def run_experiments(
    g: nx.Graph,
    output_dir: Path,
    n_requests: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Evaluate:
        shortest_hop
        min_latency
        max_reliability
        student_policy

    Offered loads:
        0.02, 0.05, 0.10, 0.15 requests/ms

    Important:
    At one offered-load value, ALL policies must receive the SAME
    generated request trace for a fair comparison.
    """

    # ===================================================================================================

    generator = random.Random(seed)

    loads = [0.02, 0.05, 0.10, 0.15]
    policies = ["shortest_hop", "min_latency", "max_reliability", "student_policy"]

    global_summary = []
    global_link = []

    # ===================================================================================================

    for load in loads:
        requests = generate_requests(g, n_requests, load, generator)

        for policy in policies:
            request_df, link_df = simulate(g, requests, policy, seed)

            request_summary = summarize(request_df, load)
            df_request_summary = pd.DataFrame(request_summary)

            # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.itertuples.html#pandas-dataframe-itertuples

            for row in df_request_summary.itertuples():
                global_summary.append(row)

            for row in link_df.itertuples():
                global_link.append(row)

    # ===================================================================================================

    global_summary = pd.DataFrame(global_summary)
    global_link = pd.DataFrame(global_link)

    # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html#pandas-dataframe-to-csv
    
    global_link.to_csv(output_dir / "links.csv")
    global_summary.to_csv(output_dir / "summary.csv")

    return global_summary

    # TODO 6A:
    # - Generate one request trace per load.
    # - Run all four policies on the same trace.
    # - Save per-request and per-link CSV files.
    # - Save and return summary.csv.
    raise NotImplementedError("Complete Task 6A")


def plot_metric(
    summary_df: pd.DataFrame,
    metric: str,
    ylabel: str,
    path: Path,
) -> None:
    """Provided plotting helper."""
    display_names = {
        "shortest_hop": "Minimum Hop",
        "min_latency": "Minimum Latency",
        "max_reliability": "Maximum Reliability",
        "student_policy": "Student Policy",
    }

    plt.figure(figsize=(6.8, 4.4))
    for policy, group in summary_df.groupby("policy"):
        group = group.sort_values("offered_load")
        offered_load_per_s = 1000.0 * group["offered_load"]
        plt.plot(
            offered_load_per_s,
            group[metric],
            marker="o",
            linewidth=1.6,
            markersize=5,
            label=display_names.get(policy, policy),
        )

    plt.xlabel("Offered Load (requests/s)")
    plt.ylabel(ylabel)
    plt.grid(axis="y", linewidth=0.5, alpha=0.35)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(path, dpi=240, bbox_inches="tight")
    plt.close()


def make_plots(summary_df: pd.DataFrame, output_dir: Path) -> None:
    """
    Required figures:
      1. success rate vs offered load
      2. average latency vs offered load
      3. throughput vs offered load
      4. average waiting time vs offered load
    """
    # TODO 6B:
    # Call plot_metric(...) for all four required metrics.

    plot_metric(summary_df, "success_rate", "Success Rate", output_dir / "success_rate_v_offered_load.png")
    plot_metric(summary_df, "avg_latency_ms", "Average Latency (ms)", output_dir / "avg_latency_v_offered_load.png")
    plot_metric(summary_df, "throughput_req_per_s", "Throughput (requests/s)", output_dir / "throughput_v_offered_load.png")
    plot_metric(summary_df, "avg_waiting_ms", "Average Waiting Time (ms)", output_dir / "avg_waiting_v_offered_load.png")

    return None
    raise NotImplementedError("Complete Task 6B")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topology", default="../data/topology.json")
    parser.add_argument("--output", default="../outputs/student_run")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    g = load_topology(Path(args.topology))
    draw_topology(g, output_dir / "topology.png")

    summary_df = run_experiments(
        g,
        output_dir,
        n_requests=args.requests,
        seed=args.seed,
    )
    make_plots(summary_df, output_dir)

    print(summary_df.to_string(index=False))
    print(f"\nResults saved to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
