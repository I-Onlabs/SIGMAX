#!/usr/bin/env bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping SIGMAX...${NC}\n"

# Function to stop process by PID file
stop_process() {
    local pid_file=$1
    local name=$2

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${CYAN}Stopping $name (PID: $pid)...${NC}"
            kill $pid
            rm "$pid_file"
            echo -e "${GREEN}✓ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name not running${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found for $name${NC}"
    fi
}

# Stop SIGMAX components
stop_process "sigmax.pid" "SIGMAX Core"
stop_process "api.pid" "API Server"
stop_process "ui.pid" "UI Server"

# Stop containers
if command -v podman-compose >/dev/null 2>&1; then
    echo -e "\n${CYAN}Stopping containers...${NC}"
    podman-compose down
    echo -e "${GREEN}✓ Containers stopped${NC}"
elif command -v docker-compose >/dev/null 2>&1; then
    echo -e "\n${CYAN}Stopping containers...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Containers stopped${NC}"
fi

echo -e "\n${GREEN}✅ SIGMAX stopped successfully${NC}\n"
