# FRIDAY AI Monitoring & Health Check System

## Overview
This document describes the automated monitoring system for FRIDAY AI to ensure continuous operation and self-healing capabilities.

## Components Monitored
1. Voice Pipeline Health
2. Vision System Status  
3. LLM Backend Availability
4. Audio Stream Processing
5. Database Connectivity
6. WebSocket Connections
7. System Resource Usage

## Health Check Endpoints
- `GET /health` - Overall system health
- `GET /api/v1/status` - Voice pipeline status
- `GET /api/v1/vision/status` - Vision system status
- `GET /api/v1/llm/generate?test=ping` - LLM backend test

## Automated Recovery Actions
1. Restart voice pipeline on failure
2. Reinitialize vision engine if frame processing stalls
3. Switch LLM backend if primary fails
4. Reconnect audio stream if dropped
5. Clear database connections if needed

## Monitoring Frequency
- Health checks: Every 30 seconds
- Deep diagnostics: Every 5 minutes
- Performance metrics: Every minute
- Alert thresholds: Configurable

## Implementation Files
- `src/friday/monitoring/__init__.py` - Main monitoring orchestrator
- `src/friday/monitoring/health_checker.py` - Health check logic
- `src/friday/monitoring/auto_healer.py` - Self-healing mechanisms
- `src/friday/monitoring/metrics_collector.py` - Performance tracking
- `frontend/src/hooks/use-health-monitor.ts` - Frontend health display

## Setup Instructions
1. Install monitoring dependencies:
   ```bash
   pip install psutil prometheus-client
   ```
2. Add to requirements.txt
3. Initialize monitoring in main.py startup
4. Configure alert thresholds in config/settings.py