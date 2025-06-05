#!/bin/bash

# OneCode Plant CLI - Code formatting script
# This script formats Python code using black and isort, and checks with flake8

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_DIRS=("onecode" "tests" "examples")
EXCLUDE_PATTERNS=("*/.venv/*" "*/build/*" "*/install/*" "*/log/*")

# Default options
FIX_MODE=false
CHECK_ONLY=false
VERBOSE=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Format Python code in the OneCode Plant CLI project.

OPTIONS:
    -f, --fix       Apply formatting fixes (default: dry-run)
    -c, --check     Check only, don't format (exit with error if changes needed)
    -v, --verbose   Verbose output
    -h, --help      Show this help message

FORMATTERS:
    - black: Code formatter
    - isort: Import sorter
    - flake8: Linter (check only)

EXAMPLES:
    $0                  # Dry-run, show what would be changed
    $0 --fix            # Apply all formatting fixes
    $0 --check          # Check formatting, exit 1 if changes needed
    $0 --fix --verbose  # Apply fixes with verbose output

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--fix)
            FIX_MODE=true
            shift
            ;;
        -c|--check)
            CHECK_ONLY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate conflicting options
if [[ "$FIX_MODE" == true && "$CHECK_ONLY" == true ]]; then
    print_error "Cannot use --fix and --check together"
    exit 1
fi

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_tools=()
    
    for tool in black isort flake8; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_status "Install with: pip install black isort flake8"
        exit 1
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        print_success "All dependencies available"
        for tool in black isort flake8; do
            version=$($tool --version 2>/dev/null | head -n1)
            echo "  $tool: $version"
        done
    fi
}

# Build file list for processing
build_file_list() {
    print_status "Building file list..."
    
    local files=()
    
    # Find Python files in specified directories
    for dir in "${PYTHON_DIRS[@]}"; do
        local dir_path="$PROJECT_ROOT/$dir"
        if [[ -d "$dir_path" ]]; then
            while IFS= read -r -d '' file; do
                files+=("$file")
            done < <(find "$dir_path" -name "*.py" -type f -print0)
        fi
    done
    
    # Apply exclusion patterns
    local filtered_files=()
    for file in "${files[@]}"; do
        local exclude=false
        for pattern in "${EXCLUDE_PATTERNS[@]}"; do
            if [[ "$file" == $pattern ]]; then
                exclude=true
                break
            fi
        done
        
        if [[ "$exclude" == false ]]; then
            filtered_files+=("$file")
        fi
    done
    
    printf '%s\n' "${filtered_files[@]}"
}

# Run black formatter
run_black() {
    local files=("$@")
    local black_args=()
    
    if [[ "$CHECK_ONLY" == true ]]; then
        black_args+=("--check" "--diff")
        print_status "Checking code formatting with black..."
    elif [[ "$FIX_MODE" == true ]]; then
        print_status "Formatting code with black..."
    else
        black_args+=("--check" "--diff")
        print_status "Checking code formatting with black (dry-run)..."
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        black_args+=("--verbose")
    fi
    
    black_args+=("--line-length" "88")
    black_args+=("--target-version" "py38")
    black_args+=("${files[@]}")
    
    if black "${black_args[@]}"; then
        print_success "Black formatting check passed"
        return 0
    else
        if [[ "$CHECK_ONLY" == true || "$FIX_MODE" == false ]]; then
            print_warning "Black formatting issues found"
        else
            print_error "Black formatting failed"
        fi
        return 1
    fi
}

# Run isort import sorter
run_isort() {
    local files=("$@")
    local isort_args=()
    
    if [[ "$CHECK_ONLY" == true ]]; then
        isort_args+=("--check-only" "--diff")
        print_status "Checking import sorting with isort..."
    elif [[ "$FIX_MODE" == true ]]; then
        print_status "Sorting imports with isort..."
    else
        isort_args+=("--check-only" "--diff")
        print_status "Checking import sorting with isort (dry-run)..."
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        isort_args+=("--verbose")
    fi
    
    # Configure isort to be compatible with black
    isort_args+=("--profile" "black")
    isort_args+=("--multi-line" "3")
    isort_args+=("--line-length" "88")
    isort_args+=("--force-grid-wrap" "0")
    isort_args+=("--use-parentheses")
    isort_args+=("--ensure-newline-before-comments")
    isort_args+=("${files[@]}")
    
    if isort "${isort_args[@]}"; then
        print_success "Isort check passed"
        return 0
    else
        if [[ "$CHECK_ONLY" == true || "$FIX_MODE" == false ]]; then
            print_warning "Import sorting issues found"
        else
            print_error "Import sorting failed"
        fi
        return 1
    fi
}

# Run flake8 linter
run_flake8() {
    local files=("$@")
    print_status "Checking code quality with flake8..."
    
    local flake8_args=()
    
    if [[ "$VERBOSE" == true ]]; then
        flake8_args+=("--verbose")
    fi
    
    # Configure flake8
    flake8_args+=("--max-line-length" "88")
    flake8_args+=("--extend-ignore" "E203,W503")  # Compatible with black
    flake8_args+=("--max-complexity" "10")
    flake8_args+=("--statistics")
    flake8_args+=("${files[@]}")
    
    if flake8 "${flake8_args[@]}"; then
        print_success "Flake8 check passed"
        return 0
    else
        print_error "Flake8 found issues"
        return 1
    fi
}

# Main execution
main() {
    print_status "OneCode Plant CLI - Code Formatter"
    print_status "Project root: $PROJECT_ROOT"
    
    if [[ "$VERBOSE" == true ]]; then
        print_status "Mode: $(if [[ "$CHECK_ONLY" == true ]]; then echo "check-only"; elif [[ "$FIX_MODE" == true ]]; then echo "fix"; else echo "dry-run"; fi)"
        print_status "Python directories: ${PYTHON_DIRS[*]}"
        print_status "Exclude patterns: ${EXCLUDE_PATTERNS[*]}"
    fi
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check dependencies
    check_dependencies
    
    # Build file list
    local files
    mapfile -t files < <(build_file_list)
    
    if [[ ${#files[@]} -eq 0 ]]; then
        print_warning "No Python files found to format"
        exit 0
    fi
    
    print_status "Found ${#files[@]} Python files to process"
    
    if [[ "$VERBOSE" == true ]]; then
        printf '  %s\n' "${files[@]}"
    fi
    
    # Run formatters
    local exit_code=0
    
    # Run isort first (import sorting)
    if ! run_isort "${files[@]}"; then
        exit_code=1
    fi
    
    # Run black (code formatting)
    if ! run_black "${files[@]}"; then
        exit_code=1
    fi
    
    # Run flake8 (linting)
    if ! run_flake8 "${files[@]}"; then
        exit_code=1
    fi
    
    # Summary
    if [[ $exit_code -eq 0 ]]; then
        print_success "All formatting checks passed!"
    else
        if [[ "$FIX_MODE" == true ]]; then
            print_error "Some formatting operations failed"
        else
            print_warning "Formatting issues found. Run with --fix to apply changes."
        fi
    fi
    
    exit $exit_code
}

# Execute main function
main "$@"
