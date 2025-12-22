#!/usr/bin/env bash
#
# SIGMAX CLI Installation Script
#
# Usage:
#   ./install.sh              # Install in current environment
#   ./install.sh --user       # Install for current user only
#   ./install.sh --dev        # Install in development mode
#   ./install.sh --pipx       # Install using pipx (recommended)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python version
check_python() {
    print_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        print_error "Python 3.10 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION detected"
}

# Install using pip
install_pip() {
    local MODE=$1

    print_info "Installing SIGMAX CLI using pip..."

    if [ "$MODE" == "dev" ]; then
        pip install -e ".[dev]"
        print_success "Installed in development mode"
    elif [ "$MODE" == "user" ]; then
        pip install --user .
        print_success "Installed for current user"
    else
        pip install .
        print_success "Installed globally"
    fi
}

# Install using pipx
install_pipx() {
    print_info "Installing SIGMAX CLI using pipx..."

    if ! command -v pipx &> /dev/null; then
        print_warning "pipx is not installed. Installing pipx..."
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    fi

    pipx install .
    print_success "Installed using pipx (isolated environment)"
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    if command -v sigmax &> /dev/null; then
        VERSION=$(sigmax version | grep -oP '(?<=version )[0-9.]+')
        print_success "SIGMAX CLI v$VERSION installed successfully"
        return 0
    else
        print_error "Installation verification failed"
        print_info "You may need to restart your shell or add the installation directory to PATH"
        return 1
    fi
}

# Show post-install instructions
show_instructions() {
    echo ""
    echo "╭────────────────────────────────────────────────────────────╮"
    echo "│                SIGMAX CLI Installation Complete             │"
    echo "╰────────────────────────────────────────────────────────────╯"
    echo ""
    print_info "Quick Start:"
    echo "  1. Configure API credentials:"
    echo "     $ sigmax config set api_url http://localhost:8000"
    echo "     $ sigmax config set api_key sk-your-api-key"
    echo ""
    echo "  2. Analyze a trading pair:"
    echo "     $ sigmax analyze BTC/USDT"
    echo ""
    echo "  3. Check system status:"
    echo "     $ sigmax status"
    echo ""
    echo "  4. Start interactive shell:"
    echo "     $ sigmax shell"
    echo ""
    print_info "For more help:"
    echo "     $ sigmax --help"
    echo "     $ sigmax <command> --help"
    echo ""
}

# Main installation flow
main() {
    echo "╭────────────────────────────────────────────────────────────╮"
    echo "│            SIGMAX CLI Installation Script                  │"
    echo "╰────────────────────────────────────────────────────────────╯"
    echo ""

    # Parse arguments
    MODE="normal"
    for arg in "$@"; do
        case $arg in
            --user)
                MODE="user"
                ;;
            --dev)
                MODE="dev"
                ;;
            --pipx)
                MODE="pipx"
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --user    Install for current user only"
                echo "  --dev     Install in development mode (editable)"
                echo "  --pipx    Install using pipx (recommended, isolated)"
                echo "  --help    Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $arg"
                echo "Run '$0 --help' for usage"
                exit 1
                ;;
        esac
    done

    # Run installation
    check_python

    if [ "$MODE" == "pipx" ]; then
        install_pipx
    else
        install_pip "$MODE"
    fi

    verify_installation
    show_instructions
}

# Run main
main "$@"
