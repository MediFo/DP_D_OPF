# Edge Device and Network Configuration Guide

## Overview

This document explains the edge device configuration system used for simulating heterogeneous edge computing environments for distributed Optimal Power Flow (OPF) evaluation.

The configuration is stored in `edge_devices_config.json` and defines **36 diverse edge devices** organized into **6 device types** with varied network characteristics.

---

## Device Type Categories

The 36 devices are organized into 6 categories, with **100% focus on medium and small devices**:

### 1. **Industrial Controllers** (7 devices - 19.4%)
**Tier:** Standard (Medium)
**Network:** Fast Ethernet, Gigabit Ethernet
**Use Cases:** Factory automation, SCADA systems, Process control

**Characteristics:**
- Moderate compute (2-8 cores)
- Medium memory (4-32 GB)
- Ruggedized for harsh environments
- Medium power consumption (35-180W max)
- Compute efficiency: 0.68x - 1.05x
- High reliability: 0.90 - 0.97

**Example Devices:**
- Siemens SIMATIC IPC627E: 4 cores @ 2.0GHz, 8GB RAM, Ethernet Fast
- Dell Edge Gateway 5200: 4 cores @ 1.9GHz, 8GB RAM
- Advantech ARK-2250: 2 cores @ 1.8GHz, 4GB RAM (Fanless)
- Beckhoff C6015: 2 cores @ 1.75GHz, 4GB RAM (Ultra-compact)
- Stratus ztC Edge: 8 cores @ 2.8GHz, 32GB RAM (Virtualized)

---

### 2. **Enterprise Servers** (7 devices - 19.4%)
**Tier:** Standard (Medium)
**Network:** Gigabit Ethernet
**Use Cases:** Branch office computing, Local data processing, Business applications

**Characteristics:**
- Moderate compute (4-8 cores)
- Medium memory (12-32 GB)
- Office/enterprise environments
- Power consumption (55-170W max)
- Compute efficiency: 0.92x - 1.08x
- Reliability: 0.91 - 0.96

**Example Devices:**
- Intel NUC Mini PC: 4 cores @ 2.4GHz, 16GB RAM
- Cisco IOx Gateway: 4 cores @ 2.5GHz, 12GB RAM
- Fujitsu PRIMERGY TX1320: 6 cores @ 3.0GHz, 16GB RAM
- HPE ProLiant MicroServer Gen10: 8 cores @ 3.2GHz, 32GB RAM
- Lenovo ThinkEdge SE70: 8 cores @ 2.8GHz, 32GB RAM

---

### 3. **AI/ML Platforms** (5 devices - 13.9%)
**Tier:** Standard/Basic (Mixed)
**Network:** Gigabit Ethernet, WiFi AC
**Use Cases:** Computer vision, Real-time inference, Edge AI analytics

**Characteristics:**
- AI acceleration capabilities
- Variable compute (2-8 cores)
- Power efficient (10-250W max)
- Mixed network connectivity
- Compute efficiency: 0.70x - 1.18x
- Reliability: 0.84 - 0.95

**Example Devices:**
- NVIDIA Jetson AGX Xavier: 8 cores @ 2.26GHz, 32GB RAM, 60W (Standard)
- Google Coral Dev Board: 4 cores @ 1.5GHz, 4GB RAM, WiFi AC
- NVIDIA Jetson Nano: 4 cores @ 1.43GHz, 4GB RAM, 10W (Basic)
- BeagleBone AI-64: 2 cores @ 2.0GHz, 4GB RAM (Basic)
- Neousys Nuvo-8240GC: 8 cores @ 3.2GHz, 32GB RAM (GPU-accelerated)

---

### 4. **IoT Gateways** (8 devices - 22.2%)
**Tier:** Basic (Small)
**Network:** Ethernet Fast, WiFi N, LTE
**Use Cases:** Sensor data aggregation, Protocol translation, IoT management

**Characteristics:**
- Low compute (1-4 cores)
- Small memory (2-4 GB)
- Very low power (20-40W max)
- Mixed network (wired/wireless/cellular)
- Compute efficiency: 0.50x - 0.75x
- Reliability: 0.85 - 0.92

**Example Devices:**
- Moxa MC-1100: 1 core @ 1.2GHz, 2GB RAM, 20W (RISC-based)
- Advantech UNO-2271G: 2 cores @ 1.6GHz, 4GB RAM
- Portwell WEBS-2170: 4 cores @ 2.0GHz, 4GB RAM, LTE
- Axiomtek eBOX800-FL: 2 cores @ 1.6GHz, 4GB RAM (Fanless)
- Siemens IOT2040: 2 cores @ 1.7GHz, 2GB RAM
- Cisco IR829: 2 cores @ 1.5GHz, 2GB RAM, LTE

---

### 5. **Wireless Edge** (5 devices - 13.9%)
**Tier:** Basic (Small)
**Network:** WiFi AC, WiFi N
**Use Cases:** Mobile edge computing, Temporary deployments, Wireless sensors

**Characteristics:**
- Low power consumption (12-16W max)
- WiFi connectivity only
- Compact form factor
- Memory: 4-8 GB
- Compute efficiency: 0.62x - 0.82x
- Reliability: 0.81 - 0.86

**Example Devices:**
- Raspberry Pi 4 (8GB): 4 cores @ 1.5GHz, WiFi AC, 15W
- Raspberry Pi 5: 4 cores @ 2.4GHz, WiFi AC, 12W
- Asus Tinker Board 2: 4 cores @ 1.8GHz, WiFi N
- Rock Pi 4C Plus: 6 cores @ 2.0GHz, WiFi N
- Orange Pi 5: 8 cores @ 2.4GHz, WiFi AC

---

### 6. **Embedded/Development Platforms** (4 devices - 11.1%)
**Tier:** Basic (Small)
**Network:** WiFi AC, WiFi N
**Use Cases:** Prototyping, Education, Hobby projects, Edge experimentation

**Characteristics:**
- Very low power (8-15W max)
- Small memory (2-4 GB)
- Development-focused
- WiFi connectivity
- Compute efficiency: 0.55x - 0.75x
- Reliability: 0.79 - 0.82

**Example Devices:**
- Arduino Portenta X8: 4 cores @ 1.8GHz, 2GB RAM, 8W
- Odroid N2+: 6 cores @ 2.4GHz, 4GB RAM
- Pine64 ROCKPro64: 6 cores @ 2.0GHz, 4GB RAM
- Banana Pi M5: 4 cores @ 2.0GHz, 4GB RAM

---

## Device Tier Distribution

| Tier | Count | Percentage | Description |
|------|-------|------------|-------------|
| **Standard** | 16 | 44.4% | Medium enterprise/industrial devices |
| **Basic** | 20 | 55.6% | Small IoT/embedded/wireless devices |

**Total:** 36 devices with **100% focus on medium (44.4%) and small (55.6%) devices**

---

## Network Profiles

The system supports 7 network types with varying characteristics:

| Network Type | Bandwidth | Latency | Packet Loss | Description |
|--------------|-----------|---------|-------------|-------------|
| **fiber** | 1000 Mbps | 2 ms | 0.01% | High-speed fiber optic |
| **ethernet_gigabit** | 1000 Mbps | 5 ms | 0.05% | Gigabit Ethernet |
| **ethernet_fast** | 100 Mbps | 10 ms | 0.1% | Fast Ethernet 100Mbps |
| **wifi_ac** | 300 Mbps | 15 ms | 0.2% | WiFi 802.11ac |
| **wifi_n** | 100 Mbps | 25 ms | 0.5% | WiFi 802.11n |
| **lte** | 50 Mbps | 40 ms | 1.0% | 4G LTE cellular |
| **low_bandwidth** | 10 Mbps | 60 ms | 2.0% | Low bandwidth connection |

### Network Type Distribution

| Network Type | Device Count | Usage |
|--------------|--------------|-------|
| **ethernet_gigabit** | 12 devices | Enterprise, industrial |
| **ethernet_fast** | 10 devices | Industrial, IoT gateways |
| **wifi_ac** | 8 devices | Wireless edge, dev platforms |
| **wifi_n** | 4 devices | Low-cost wireless devices |
| **lte** | 2 devices | Mobile/field deployments |

---

## Performance Characteristics

Each device has 4 performance metrics that affect simulation behavior:

### 1. **Compute Efficiency** (0.50x - 1.28x)
- Affects CPU utilization inversely
- Higher efficiency = Lower CPU usage for same workload
- **Example:** Device with 0.60x uses **67% more CPU** than baseline
- **Example:** Device with 1.20x uses **17% less CPU** than baseline

### 2. **Memory Efficiency** (0.58x - 1.20x)
- Affects memory usage inversely
- Higher efficiency = Lower memory consumption
- **Example:** Device with 0.70x uses **43% more memory**
- **Example:** Device with 1.15x uses **13% less memory**

### 3. **Workload Capacity** (0.35x - 1.8x)
- Determines data processing volume
- Affects network traffic volume
- **Example:** Device with 0.5x handles **half** the data traffic
- **Example:** Device with 1.8x handles **80% more** data traffic

### 4. **Reliability** (0.79 - 0.97)
- Device dependability rating
- Affects simulation outcomes
- Enterprise/Industrial devices: 0.90-0.97 (high)
- IoT/Embedded devices: 0.79-0.92 (moderate to high)

---

## Hardware Diversity

| Metric | Minimum | Maximum | Range |
|--------|---------|---------|-------|
| **CPU Cores** | 1 | 8 | 8x |
| **CPU Frequency** | 1.2 GHz | 3.2 GHz | 2.7x |
| **Memory** | 2 GB | 32 GB | 16x |
| **Storage** | 16 GB | 512 GB | 32x |
| **Max Power** | 8W | 250W | 31x |
| **Compute Efficiency** | 0.50x | 1.18x | 2.36x |
| **Workload Capacity** | 0.35x | 1.3x | 3.7x |

---

## Topology-Based Network Connections

The system creates network links between edge devices based on the **power grid topology** from MATPOWER case files, NOT full mesh.

### How It Works:

1. Each edge device corresponds to a bus in the power system
2. Network links are created only between connected buses (neighbors)
3. Link characteristics determined by device network types (bottleneck principle)

### Example: IEEE 30-Bus Case

```
Traditional Full Mesh: 30 × 29 / 2 = 435 links
Topology-Based: 41 transmission lines = 82 bidirectional links

Reduction: 81% fewer network links!
```

### Network Link Creation:

```
Bus 1 ↔ Bus 2:
  Device 1: ethernet_fast (100 Mbps)
  Device 2: ethernet_fast (100 Mbps)
  → Link: ~98 Mbps (variation applied)

Bus 4 ↔ Bus 7:
  Device 4: ethernet_fast (100 Mbps)
  Device 7: ethernet_gigabit (1000 Mbps)
  → Link: ~95 Mbps (ethernet_fast bottleneck)

Bus 10 ↔ Bus 20:
  Device 10: ethernet_gigabit (1000 Mbps)
  Device 20: ethernet_fast (100 Mbps)
  → Link: ~100 Mbps (ethernet_fast bottleneck)
```

**Random Variation:** Each link has ±10% random variation for realism

---

## Resource Utilization Scaling

The simulation scales CPU/memory usage based on device characteristics:

### CPU Usage Formula:
```
Scaled CPU = Base CPU × (1.0 / compute_efficiency) × random(0.95, 1.05)
```

### Memory Usage Formula:
```
Scaled Memory = Base Memory × (1.0 / memory_efficiency) × random(0.95, 1.05)
```

### Network Traffic Formula:
```
Scaled Traffic = Base Traffic × workload_capacity × random(0.85, 1.15)
```

### Real Example (50% baseline CPU load):

| Device | Compute Eff | Actual CPU Usage |
|--------|-------------|------------------|
| Moxa MC-1100 | 0.50x | ~100% (maxed out) |
| Raspberry Pi 4 | 0.65x | ~75% |
| Intel NUC | 0.95x | ~52% |
| Dell PowerEdge XR2 | 1.28x | ~39% (efficient) |

---

## Usage Examples

### Basic Usage:
```bash
# Automatically uses first 30 devices from config
python evaluate_edge_opf.py --mode comparison --servers 30 --case testbeds/pglib_opf_case30_ieee.m
```

### Output Example:
```
Setting up edge infrastructure with 30 servers...
Loaded 36 device configurations from edge_devices_config.json
Loaded 7 network profiles

  Server 1: Siemens SIMATIC IPC627E
    - Device Type: industrial_controller
    - Tier: standard, Network: ethernet_fast
    - CPU: 4 cores @ 2.0 GHz
    - Compute Efficiency: 0.85x

  Server 20: Moxa MC-1100
    - Device Type: iot_gateway
    - Tier: basic, Network: ethernet_fast
    - CPU: 1 core @ 1.2 GHz
    - Compute Efficiency: 0.50x

  Creating network links:
    Using topology from: pglib_opf_case30_ieee.m
    Grid: 30 buses, 41 lines

    Link 1↔2: 987 Mbps, 5.2ms latency
    Link 10↔20: 54 Mbps, 43.4ms latency (LTE bottleneck)
    Link 20↔21: 97 Mbps, 9.7ms latency

✓ Created 30 edge servers and 82 network links (topology-based)
```

---

## Customization

### To Add New Devices:

1. Open `edge_devices_config.json`
2. Add new device to the `devices` array
3. Specify:
   - `device_type`: One of the 6 types
   - `tier`: standard/basic
   - `network_type`: One of 7 network profiles
   - `specs`: Hardware specifications
   - `performance`: Performance characteristics

### To Modify Device Types:

Edit the `device_types` section to change categories, descriptions, or use cases.

### To Add Network Profiles:

Add new profile to `network_profiles` section with bandwidth, latency, and packet loss specifications.

---

## Summary Statistics

**Total Devices:** 36

**Tier Distribution:**
- Standard (Medium): 16 devices (44.4%)
- Basic (Small): 20 devices (55.6%)

**Device Type Distribution:**
- Industrial Controllers: 7 (19.4%)
- Enterprise Servers: 7 (19.4%)
- AI/ML Platforms: 5 (13.9%)
- IoT Gateways: 8 (22.2%)
- Wireless Edge: 5 (13.9%)
- Embedded/Dev: 4 (11.1%)

**Power Consumption Range:** 8W - 250W (31x variation)
**CPU Core Range:** 1 - 8 cores (8x variation)
**Memory Range:** 2GB - 32GB (16x variation)
**Network Bandwidth Range:** 50 Mbps - 1000 Mbps (20x variation)
**Latency Range:** 10ms - 60ms (6x variation)

This creates a **highly heterogeneous and realistic edge computing environment** for evaluating distributed OPF algorithms on diverse hardware with varied network conditions.
