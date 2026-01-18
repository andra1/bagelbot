# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BagelBot is a Python automation scaffold for placing scheduled orders based on a drop event from Holey Dough bagel shop in Chicago. The core flow is: listen for event drop → fetch menu → build cart → checkout.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
