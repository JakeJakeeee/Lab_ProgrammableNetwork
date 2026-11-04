# Programmable Network Labs

A repository containing network configurations described as data, built, and documented automatically by Python scripts. This project covers both Layer 2 switched networks and Layer 3 statically routed networks, focusing on automated network provisioning and topology design.

## Live Documentation

* [Lab 1 & 2 Documentation](https://jakejakeeee.github.io/Lab_ProgrammableNetwork/)
* [Lab 3 Documentation](https://jakejakeeee.github.io/Lab_ProgrammableNetwork/week3/)

---

## Lab 1 & 2: Switched Network (Layer 2)

This lab implements a small Layer 2 switched network to demonstrate programmable topology generation, MAC learning, and duplicate address detection (DAD) across IPv4 and IPv6.

### The Network
| Part | Details |
|---|---|
| Switches | 3 (`s1`, `s2`, `s3`) |
| Hosts | 6 (`h1` to `h6`), each with IPv4 and IPv6 addresses |

### Files & Architecture
| File | What it does |
|---|---|
| `topology.yaml` | Describes the network: switches, hosts, addresses, links |
| `build_topo.py` | Runs `check()` to catch bad data (duplicate IPs/MACs, missing links), then builds the network in Mininet |
| `make_page.py` | Reads `topology.yaml` and `page.yaml`, draws the diagram, and writes `docs/index.html` |
| `page.yaml` | Holds the text for the web page (reflection answers) |

### Evidence & Validation
| File | What it proves |
|---|---|
| `evidence/pingall.txt` | All hosts can reach each other (0% loss), proving basic connectivity |
| `evidence/macs.txt` | Switches successfully learned MAC addresses on host ports and trunk ports |
| `evidence/dad.txt` | IPv6 successfully flagged a duplicate address (`dadfailed`); IPv4 accepted it silently |
| `evidence/check.txt` | The `check()` function successfully caught bad data before the network was built |
| `evidence/neigh.txt` | Hosts learned which MAC address belongs to each IP (ARP for IPv4, neighbor discovery for IPv6) |

---

## Lab 3: Routed Network (Layer 3)

The Week 3 lab implements a statically routed Layer 3 network to demonstrate manual route calculation, failure scenarios, and routing efficiency.

### Topology & Design
* **Topology & Redundancy:** The network is built using a diamond topology consisting of 4 routers (r1, r2, r3, r4) and 4 host LANs. Routers r1 and r4 are connected via two parallel physical paths (through r2 and r3). This creates a physical redundant loop, ensuring a backup path exists in the event of a link failure.
* **Addressing Scheme:** The network operates on the `10.8.0.0/16` block. 
  * Point-to-point router links utilize `/30` subnets to conserve IP addresses, as they provide exactly two usable IPs per link. 
  * Host LANs utilize `/24` subnets, with routers assigned the `.1` address and hosts assigned the `.10` address for standardized configuration.
* **Route Summarization:** IP addresses 10.8.32.0/24 and 10.8.33.0/24 are chosen to demonstrate route summarization. A single 10.8.32.0/23 route covers both LANs, which keeps the routing tables smaller and simpler.
  
### Files & Architecture
| File | What it does |
|---|---|
| `network.yaml` | Describes the Layer 3 network: routers, LANs, addresses, links, and static routes |
| `page3.yaml` | Holds the reflection answers explaining the topology design, route summarization logic, and failure analysis |
| `make_page3.py` | Parses the YAML files, validates the network logic, and automatically generates `docs/week3/index.html` |

### Evidence & Validation
| File | What it proves |
|---|---|
| `evidence3/routes.txt` | Displays the final routing table (`ip route`) configured on every router |
| `evidence3/traces.txt` | Shows `traceroute` output proving successful pathing from one host to every other host |
| `evidence3/summary.txt` | Uses `ip route get` to prove the `/23` summary route correctly directs traffic for multiple `/24` LANs |
| `evidence3/failure.txt` | Demonstrates that manual static routes fail to recover automatically when a link is brought down |
| `evidence3/check.txt` | Shows the pre-flight validation successfully catching routing loops and missing routes before the network is built |

---
### Week 4
1. Why did the first firewall rule in Step 3 have no effect, and why does blocking h1 → h3 also break h3 → h1?
* The first firewall rule had no effect because the rule and the forwarding rule for h3 both matched an h1 to h3 ping, and both had the default priority of 32768. OpenFlow doesn’t define which of two equal-priority overlapping rules wins, so the forwarding rule won and the drop rule stayed at n_packets=0. Raising the drop rule to priority 40000 made it win every time. Blocking h1 to h3 also breaks h3 to h1 because a rule matches headers, not intentions. When h3 pings h1, h1’s reply has source 10.8.0.1 and destination 10.8.0.3, exactly what the drop rule matches, so the reply is dropped and h3 never hears back.

2. In Step 5, why did one conversation survive the controller failure and another didn't?
* The h1 to h2 conversation survived because the controller had already installed flows for it in the switch, so the switch could forward without asking the controller. The h1 to h3 conversation failed because no flow existed, so the table-miss rule sent the packet to a controller that was no longer there. After about a minute, h1 to h2 failed too, because its flows had an idle timeout of 60 seconds and expired, leaving the switch needing the controller again.

3. Secure or standalone: which would you choose for a campus network, and what does the other one cost you?
* For a campus network I would choose secure mode. It keeps your policy, such as firewall rules and access control, in force even when the controller is down. The cost is that the network slowly stops working while the controller is down. New connections fail right away. Old connections keep working for a while, then stop when their rules expire after 60 seconds. We can reduce that cost with a replicated controller cluster and proactive rules. Standalone costs in security. Traffic keeps flowing, and the switch stops following the rules, so blocked traffic can get through again. Standalone is only suitable if there are no rules to enforce and uptime matters most.
