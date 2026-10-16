# Lab 1 & 2

A small network described as data, then built and documented by scripts.

## Live Documentation

[View Published Network Documentation](https://jakejakeeee.github.io/Lab_ProgrammableNetwork/)

## How to run

Build the network from `topology.yaml`:

```bash
python3 build_topo.py topology.yaml
```

## The Network

| Part | Details |
|---|---|
| Switches | 3 (`s1`, `s2`, `s3`) |
| Hosts | 6 (`h1` to `h6`), each with IPv4 and IPv6 addresses |

---

## Files

| File | What it does |
|---|---|
| `topology.yaml` | Describes the network: switches, hosts, addresses, links |
| `build_topo.py` | Runs `check()` to catch bad data (duplicate IPs or MACs, missing links), then builds the network in Mininet |
| `make_page.py` | Reads `topology.yaml` and `page.yaml`, draws the diagram, and writes `docs/index.html` |
| `page.yaml` | Holds the text for the web page (reflection answers) |

---

## Evidence

| File | What it shows |
|---|---|
| `evidence/pingall.txt` | All hosts can reach each other (0% loss) |
| `evidence/macs.txt` | Switches learned MAC addresses on host ports and trunk ports |
| `evidence/dad.txt` | IPv6 flagged a duplicate address (`dadfailed`); IPv4 accepted it silently |
| `evidence/check.txt` | `check()` caught bad data (such as duplicate IPs or invalid links) before the build |
| `evidence/neigh.txt` | Hosts learned which MAC address belongs to each IP (ARP for IPv4, neighbour discovery for IPv6) |
