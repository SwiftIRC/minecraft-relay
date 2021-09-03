# minecraft-relay

## Purpose

The purpose of this project is to relay chat between Minecraft and IRC. This is inclusive of players joining/leaving the Minecraft server or messages sent on either side.

## Requirements

Python 3.8+ (it may work on other versions but they will not be supported)

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Configuration

```bash
cp config.example.json config.json
nano config.json
```

## Usage

```bash
python3 main.py
```

## Shortcomings

This bot only supports:

- join/parts from MC, not IRC
- one IRC network
- one IRC channel
- joining IRC as an unregistered user
