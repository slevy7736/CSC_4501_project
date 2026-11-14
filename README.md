# CSC_4501_project

## TODO
- Task 1
  - base implementation done, needs testing
- Task 2
  - base implementation done, needs testing
- Task 3
  - base implementation done, needs testing
- Task 4
  - base implementation done, needs testing
- Task 5
  - Complete the main simulation loop. For every request:
    ~~1. select a route using the chosen policy;~~
    ~~2. process the links along that route in order;~~
    3. reserve link capacity and accumulate any waiting time;
    4. sample link success/failure using the provided success probability; and
    5. stop after the first failed link or record successful completion.

  - link_df with
    - policy
    - link
    - jobs
    - utilization
   
  - request_df with per-request results
    - request success rate
    - average end-to-end latency
    - average waiting time
    - average hop count
    - throughput
    - per-link utilization
- Task 6
