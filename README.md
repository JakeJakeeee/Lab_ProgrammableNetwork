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

---

### Week 7-lab (wrap up)
Q1: docker network inspect apilab shows a bridge network with the subnet 172.20.0.0/16, gateway 172.20.0.1, and the two containers api (172.20.0.2) and client (172.20.0.3), each with its own MAC address. It’s built from Week 6’s parts with each container is its own network namespace (a private network), a virtual cable connects each container to the bridge, and the Linux bridge is the virtual switch joining the two cables. Docker also adds a small DNS service, so the client can find api by name.

Q2: For a 404, 405, 400, 422 and 403, the client should fix the request or stop, because sending the same thing again always gets the same answer. A 404 means check the URL, a 405 means use a method the URL allows, a 400 means fix the broken JSON, a 422 means fix the invalid values, and a 403 means this user is not allowed, so stop or use an account with permission. A 409 means the request clashes with what already exists, so the client should read the current state and decide if anything still needs doing. A 429 means too many requests, so the client should wait the seconds in Retry-After and then try again. So the ones to never retry as they are are 400, 404, 405, 422, 403 and 409, and only the 429 is worth retrying after a wait.

Q3: It will create duplicate because, the server did the change, but the reply was lost, so the script thought it failed and sent the POST again, and POST isn’t idempotent, so it made another entry. The fix is sends the same Idempotency-Key on every attempt, so the server recognizes a repeat and replies “already done” without adding another. The key must be chosen once, before the first attempt, because the key let the server recognize that a retry is the same change as the first try. A new key on each retry would look like a new order, and the duplicates would come back.

Q4: inventory.py sent 26 requests to read my 208 devices. It read 10 devices per page, for 208 devices only neeed 21 pages, so it sent 5 more requests than pages. The extra requests were retries, because when the server answered 503 or 429 the client waited and asked for the same page again, and every retry counts as another request.

Q5: I try with the site filter for penang that return only the devices at that site. I tried it with curl and got only Penang devices, and the X-Total-Count header showed 52, so the server did the filtering and I did not have to read all 208 devices myself. I also learned that the largest limit the server accepts is 50, and that an ACL entry can only be read or deleted, never edited in place.

---

### Week 7-assignment (E4)
AI use

I used Claude (an AI assistant) for this assignment. It explained REST, idempotency and retries, helped me plan and draft sync.py, helped me debug Docker and testing problems. I ran and tested everything myself and answers against my own code and evidence.

Q1. sync.py logs in and reads the whole current state, the VLAN list and the ACL list. It compares that with intent.yaml and builds a plan before it does anything. VLANs are compared by id. VLAN 30 (guests) is in my intent but not on the API, so the plan says create-vlan 30. VLAN 10 is on both but is called users on the API and staff in my intent, so the plan says rename-vlan 10. VLAN 99 (old-guest) is on the API but not in my intent, so the plan says delete-vlan 99. VLAN 1 is never deleted. Other VLANS that is not in API but is my intent, t will create those missing VLANS. ACL entries have no id in my file, so each one is matched by everything it says (action, addresses, protocol, port and description). The entry deny 10.8.30.0/24 -> 10.8.20.0/24 tcp/22 (guests-no-ssh) was missing from the API, so it was created. After applying, the script reads the API again and builds the plan a second time, and an empty plan means it matches, which is also why a second run does nothing.

Q2. Every request goes through one function, call(), which only retries when it is safe. A GET only reads, so repeating it changes nothing. A PUT sets a VLAN to a given name, so doing it twice gives the same result as doing it once. A DELETE is safe because deleting something that is already gone returns 404, and my script treats that as success. A POST adds a new ACL entry every time, so my script retries it only because it carries an Idempotency-Key, and a POST without a key would make the script stop instead of retrying. A 401 or a 429 means the server did not process the request, so sending it again after logging in or waiting is safe. A 503 or a lost reply is the risky case, because the change may already have happened, and that is why only these safe requests are retried. After 6 tries the script gives up with an error.

Q3. For VLANs I choose the id, so a PUT says exactly what should exist and is safe to repeat. ACL entries get their id from the server and only have POST, which is not idempotent, so I had to add an Idempotency-Key. For each ACL entry, apply_step() makes a random key once, before the first attempt, and call() sends that same key on every retry of that entry. Each entry gets its own key. If I made a new key for every attempt, the server would treat each retry as a new order, so a lost reply followed by a retry would add the entry twice, which is what retry_naive.py did. If I used the same key for every run, it would go wrong the other way, because the server would replay its old answer instead of doing the new change. For example, if an entry had been deleted and my script tried to create it again, the server could say “already done” and the entry would stay missing.

Q4. Both scripts would read the API at about the same time, make different plans, and apply them. Each one only knows what it saw at the start, so the changes get mixed together. The API ends up with some of each person’s intent, which neither of them wanted. Each script’s final check would see the other person’s extra changes and report a mismatch, and if they run again, they would keep deleting each other’s work. To make this safe, the API needs to refuse a change when the data has changed since the script read it, for example with a version number that the script sends back with its change. A stale change would be rejected, and the script would read the API again and redo its plan. Also, can apply a lock while someone is reading, so only one person can change the configuration at a time.

Q5. My username and password are not in any file. sync.py reads them from the environment variables LAB_USERNAME and LAB_PASSWORD, which I set with export in the client container. The token is kept in memory inside the script and is never printed or saved. When it expires, the script logs in again. My evidence files contain only the API’s replies, not tokens. Before committing I searched my files and my git history for lab_ and for the password, to make sure no token or password is in my repository.
