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
Q1: docker network inspect apilab shows a bridge network with the subnet 172.20.0.0/16, gateway 172.20.0.1, and the two containers api (172.20.0.2) and client (172.20.0.3), each with its own MAC address. It’s built from Week 6’s parts: each container is a network namespace (its own private network), a veth pair is the cable from each one to the bridge, and the Linux bridge is the virtual switch joining them. Docker also adds a small DNS service, so the client can find api by name.

Q2: Don’t retry the ones that are your mistake, because the same request gets the same answer: 400 (fix the JSON), 404 (wrong URL), 405 (wrong method), 422 (fix the values), 403 (you’re not allowed, so stop). 409 is a clash with the current state, so read the state before deciding, and don’t repeat it blindly. 401 means log in again, then retry. 429 and 503 are the ones to retry: wait Retry-After seconds for 429, and use backoff for 503.

Q3: The server did the change, but the reply was lost, so the script thought it failed and sent the POST again, and POST isn’t idempotent, so it made another entry. Your one run made three. The fix sends the same Idempotency-Key on every attempt, so the server recognises a repeat and replies “already done” without adding another. The key must be chosen once, before the first attempt. A new key on each retry would look like a new order, and the duplicates would come back.

Q4: Your first run, with 503s, sent 26 requests, and the run with expiring tokens sent 33. Reading 208 devices at 10 per page needs only 21 requests. The extra ones are retries: 503s, 429s from the rate limit, and the 401s after tokens expired, since each retry is another request.

Q5: The site filter (?site=penang) is a good answer, because the lecture never mentioned it. You could also mention that limit goes up to 50, or that the ACL entry path allows only GET and DELETE, so entries can’t be edited in place.

---

### Week 7-assignment (E4)
AI use

I used Claude (an AI assistant) for this assignment. It explained REST, idempotency and retries, helped me plan and draft sync.py, helped me debug Docker and testing problems, and helped me draft these answers. I ran and tested everything myself and checked the answers against my own code and evidence.

Q1. How does sync.py decide what to change?

sync.py logs in and reads the whole current state: the VLAN list and the ACL list. It compares that with intent.yaml and builds a plan before it does anything. VLANs are compared by id. VLAN 30 (guests) is in my intent but not on the API, so the plan says create-vlan 30. VLAN 10 is on both but is called users on the API and staff in my intent, so the plan says rename-vlan 10. VLAN 99 (old-guest) is on the API but not in my intent, so the plan says delete-vlan 99. VLAN 1 is never deleted. ACL entries have no id in my file, so each one is identified by everything it says: action, source, destination, protocol, port and description. The entry deny 10.8.30.0/24 -> 10.8.20.0/24 tcp/22 (guests-no-ssh) was not on the API, so the plan says create-acl. An entry on the API that isn’t in my file, or a second copy of one, gets delete-acl. With --dry-run the plan is printed and the script stops. Otherwise it applies the steps, reads the state again and builds the plan a second time. If that plan is empty, the API matches my intent, and that is also why a second run does nothing.

Q2. Why is each request safe to retry?

Every request goes through one function, call(), which only retries when it is safe. A GET only reads, so repeating it changes nothing. A PUT says “VLAN 50 should be called student”, so doing it twice gives the same result as doing it once. In my chaos run VLAN 50 was created once even though the script retried. A DELETE is safe because deleting something that’s already gone gives 404, and my script treats that as success. A POST adds a new ACL entry every time, so my script retries it only because it carries an Idempotency-Key. A POST without a key would make the script stop instead of retrying, and I never send one without a key. A 401 (token expired) and a 429 (too many requests) mean the server did not process the request, so sending it again after logging in or waiting Retry-After is safe. A 503 or a lost reply is the dangerous case, because the change may already have happened, and that is where idempotent methods and keys matter. After a fixed number of tries the script gives up loudly (write the number from your own call()).

Q3. PUT vs POST, and the keys

For VLANs I choose the id, so a PUT says exactly what should exist and is safe to repeat. ACL entries get their id from the server and only have POST, which is not idempotent, so I had to add an Idempotency-Key. For each ACL entry, apply_step() makes a random key with uuid.uuid4() once, before the first attempt, and call() sends that same key on every retry of that entry. Each entry gets its own key. If I made a new key for every attempt, the server would treat each retry as a new order, so a lost reply followed by a retry would add the entry twice, which is what retry_naive.py did. If I used the same key for every run, it would go wrong the other way, because the server would replay its old answer instead of doing the new change. For example, if an entry had been deleted and my script tried to create it again, the server could say “already done” and the entry would stay missing. Using one key for all entries would get a 422, because the body differs.

Q4. Two people running sync.py at once

Both would read the API at about the same time, build different plans, and apply them. Each plan treats the other person’s entries as not wanted, so each would delete what the other just created, and the result would depend on who writes last. The API could end up with a mix of two intents that nobody asked for. To make it safe, the API needs to refuse a write when the data has changed since it was read, for example with a version number (an ETag) that the client sends back in an If-Match header, so a stale write gets a 412 and the script reads again. A lock on the whole configuration would also work, or a way to send the whole intent as one all-or-nothing change, like a candidate configuration with a commit.

Q5. Credentials

My username and password are not in any file. sync.py reads them from the environment variables LAB_USERNAME and LAB_PASSWORD, which I set with export in the client container. The token is kept in memory inside the script and is never printed or saved. When it expires, the script logs in again. My evidence files contain only the API’s replies, not tokens. Before committing I searched my files and my git history for lab_ (the start of every token) and found nothing.
