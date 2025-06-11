# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SRTgo is a Python CLI tool for automated Korean train ticket reservations (SRT and KTX). It handles:
- Automated ticket booking with retry logic
- Telegram notifications
- Credit card payment integration
- Local credential storage via keyring
- Real-time seat availability checking

## Architecture

The project consists of three main modules:

- `srtgo/srtgo.py` - Main CLI interface with interactive menus and reservation logic
- `srtgo/srt.py` - SRT (Super Rapid Train) API client with web scraping capabilities
- `srtgo/ktx.py` - KTX (Korea Train Express) API client based on Korail mobile API

Key architectural patterns:
- Uses `curl_cffi` for HTTP requests to avoid bot detection
- Implements exponential backoff with gamma distribution for retry intervals
- Stores sensitive data (credentials, payment info) locally via `keyring` module
- Uses `inquirer` for interactive CLI prompts

## Development Commands

Install development version:
```bash
pip install -e .
```

Run the application:
```bash
srtgo
```

Install from git (beta):
```bash
pip install git+https://github.com/lapis42/srtgo -U
```

## Key Implementation Details

- Both SRT and KTX modules implement similar interfaces but use different APIs
- Reservation logic includes sophisticated error handling for network issues and sold-out trains
- The main reservation loop runs continuously with random intervals to avoid detection
- Passenger types are handled via class hierarchies (Adult, Child, Senior, Disability1To3, etc.)
- Station codes are hardcoded dictionaries mapping Korean names to API codes

## Security Considerations

- All credentials are stored locally using the `keyring` library
- No network transmission of sensitive data beyond official APIs
- User-Agent strings mimic mobile applications to avoid blocking
- The code includes warnings about commercial use restrictions