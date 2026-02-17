# MachXO2 FPGA Kill-Switch Specification

**Version 1.0.0**  
**Last Updated:** February 17, 2026

---

## Overview

This document specifies the MachXO2 FPGA-based hardware kill-switch for the AIOSPANDORA/Ouroboros system, providing a physical failsafe mechanism for emergency system shutdown.

---

## 1. Purpose

Provide a hardware-based emergency shutdown mechanism that:
- Cannot be overridden by software
- Operates independently of main system
- Provides cryptographic verification
- Ensures fail-safe operation

---

## 2. Hardware Selection

**FPGA**: Lattice MachXO2-1200HC
- 1280 LUTs
- Low power (<10mW static)
- Non-volatile configuration
- Instant-on capability

---

## 3. Functional States

| State | Description | Power | LED |
|-------|-------------|-------|-----|
| INIT | Power-on initialization | ON | Blinking |
| ARMED | Normal operation | ON | Green |
| TRIGGERED | Kill-switch activated | OFF | Red |
| TAMPER | Tamper detected | OFF | Rapid Red |

---

## 4. Interface

**Inputs**:
- External trigger (GPIO, active-low)
- UART command interface (authenticated)
- Tamper sensor

**Outputs**:
- Kill signal (cuts system power)
- Status LED
- UART status reporting

---

## 5. Authentication

- HMAC-SHA256 challenge-response
- 256-bit symmetric key
- PQC-ready architecture

---

## 6. BOM Estimate

- MachXO2 FPGA: $8.50
- Supporting components: $6.50
- **Total**: ~$15 per unit

---

*See ICARUS_LATCH_POC.md for proof-of-concept implementation.*
