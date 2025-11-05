#!/usr/bin/env bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
  _____ ___ ____ __  __    _    __  __
 / ____|_ _/ ___|  \/  |  / \   \ \/ /
 \___ \| | |  _| |\/| | / _ \   \  /
  ___) | | |_| | |  | |/ ___ \  /  \
 |____/___\____|_|  |_/_/   \_\/_/\_\

 Autonomous Multi-Agent AI Trading OS
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 Starting SIGMAX deployment...${NC}\n"

# Check if running on macOS or Linux
OS="$(uname -s)"
echo -e "${CYAN}📍 Detected OS: ${OS}${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies
install_dependencies() {
    echo -e "\n${YELLOW}📦 Installing system dependencies...${NC}"

    if [[ "$OS" == "Darwin" ]]; then
        # macOS
        if ! command_exists brew; then
            echo -e "${RED}❌ Homebrew not found. Please install from https://brew.sh${NC}"
            exit 1
        fi

        echo -e "${CYAN}Installing dependencies via Homebrew...${NC}"
        brew install python@3.11 node@20 podman podman-compose || true

    elif [[ "$OS" == "Linux" ]]; then
        # Linux
        if command_exists apt-get; then
            echo -e "${CYAN}Installing dependencies via apt...${NC}"
            sudo apt-get update
            sudo apt-get install -y python3.11 python3.11-venv python3-pip nodejs npm podman podman-compose
        elif command_exists dnf; then
            echo -e "${CYAN}Installing dependencies via dnf...${NC}"
            sudo dnf install -y python3.11 nodejs npm podman podman-compose
        else
            echo -e "${RED}❌ Unsupported Linux distribution${NC}"
            exit 1
        fi
    fi

    echo -e "${GREEN}✓ System dependencies installed${NC}"
}

# Function to setup Python environment
setup_python() {
    echo -e "\n${YELLOW}🐍 Setting up Python environment...${NC}"

    cd core

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    echo -e "${CYAN}Installing Python packages...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt

    echo -e "${GREEN}✓ Python environment ready${NC}"

    deactivate
    cd ..
}

# Function to setup Node.js environment
setup_node() {
    echo -e "\n${YELLOW}📦 Setting up Node.js environment...${NC}"

    cd ui/web

    # Install dependencies
    if [ -f "package.json" ]; then
        echo -e "${CYAN}Installing npm packages...${NC}"
        npm install
        echo -e "${GREEN}✓ Node packages installed${NC}"
    fi

    cd ../..
}

# Function to setup environment file
setup_env() {
    echo -e "\n${YELLOW}⚙️  Setting up environment...${NC}"

    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env with your API keys${NC}"
    else
        echo -e "${CYAN}ℹ️  .env file already exists${NC}"
    fi
}

# Function to start services with Podman
start_services() {
    echo -e "\n${YELLOW}🐳 Starting services with Podman Compose...${NC}"

    # Check if podman-compose is available
    if command_exists podman-compose; then
        podman-compose up -d
    elif command_exists docker-compose; then
        echo -e "${CYAN}Using docker-compose instead...${NC}"
        docker-compose up -d
    else
        echo -e "${RED}❌ Neither podman-compose nor docker-compose found${NC}"
        echo -e "${YELLOW}Skipping container orchestration...${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ Services started${NC}"
}

# Function to start SIGMAX core
start_core() {
    echo -e "\n${YELLOW}🧠 Starting SIGMAX core...${NC}"

    cd core
    source venv/bin/activate

    # Start in background
    nohup python main.py --mode paper --risk-profile conservative > ../logs/sigmax.log 2>&1 &
    SIGMAX_PID=$!

    echo -e "${GREEN}✓ SIGMAX core started (PID: $SIGMAX_PID)${NC}"

    # Save PID
    echo $SIGMAX_PID > ../sigmax.pid

    deactivate
    cd ..
}

# Function to start API server
start_api() {
    echo -e "\n${YELLOW}🔌 Starting FastAPI server...${NC}"

    cd ui/api

    # Start in background
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../../logs/api.log 2>&1 &
    API_PID=$!

    echo -e "${GREEN}✓ API server started (PID: $API_PID)${NC}"

    # Save PID
    echo $API_PID > ../../api.pid

    cd ../..
}

# Function to start UI dev server
start_ui() {
    echo -e "\n${YELLOW}🎨 Starting UI dev server...${NC}"

    cd ui/web

    # Start in background
    nohup npm run dev > ../../logs/ui.log 2>&1 &
    UI_PID=$!

    echo -e "${GREEN}✓ UI dev server started (PID: $UI_PID)${NC}"

    # Save PID
    echo $UI_PID > ../../ui.pid

    cd ../..
}

# Function to display status
show_status() {
    echo -e "\n${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ SIGMAX is now running!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}\n"

    echo -e "${CYAN}📊 Access Points:${NC}"
    echo -e "  • Neural Cockpit UI:  ${YELLOW}http://localhost:3000${NC}"
    echo -e "  • API Server:         ${YELLOW}http://localhost:8000${NC}"
    echo -e "  • API Docs:           ${YELLOW}http://localhost:8000/docs${NC}"
    echo -e "  • Grafana Dashboard:  ${YELLOW}http://localhost:3001${NC} (admin/admin)"
    echo -e "  • Prometheus:         ${YELLOW}http://localhost:9090${NC}"

    echo -e "\n${CYAN}📝 Logs:${NC}"
    echo -e "  • SIGMAX Core: ${YELLOW}logs/sigmax.log${NC}"
    echo -e "  • API Server:  ${YELLOW}logs/api.log${NC}"
    echo -e "  • UI Server:   ${YELLOW}logs/ui.log${NC}"

    echo -e "\n${CYAN}🛑 To stop SIGMAX:${NC}"
    echo -e "  ${YELLOW}./stop.sh${NC}"

    echo -e "\n${GREEN}Happy Trading! 🚀${NC}\n"
}

# Main deployment flow
main() {
    echo -e "${CYAN}Starting deployment...${NC}\n"

    # Create logs directory
    mkdir -p logs

    # Check for required dependencies
    if ! command_exists python3.11 && ! command_exists python3; then
        echo -e "${YELLOW}Python 3.11 not found. Installing dependencies...${NC}"
        install_dependencies
    fi

    # Setup environments
    setup_env
    setup_python
    setup_node

    # Start services
    if [ "${SKIP_CONTAINERS:-false}" != "true" ]; then
        start_services || echo -e "${YELLOW}⚠️  Running without container orchestration${NC}"
    fi

    # Start SIGMAX components
    # Note: Uncomment these when ready to run
    # start_core
    # start_api
    # start_ui

    # Show status
    show_status

    # Open browser (optional)
    if command_exists open; then
        echo -e "${CYAN}Opening Neural Cockpit in browser...${NC}"
        sleep 3
        open http://localhost:3000
    elif command_exists xdg-open; then
        echo -e "${CYAN}Opening Neural Cockpit in browser...${NC}"
        sleep 3
        xdg-open http://localhost:3000
    fi
}

# Run main function
main "$@"
