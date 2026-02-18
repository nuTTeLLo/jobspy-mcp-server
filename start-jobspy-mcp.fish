#!/usr/bin/env fish

# Start the JobSpy MCP server container with SSE enabled in the background

# Default values
set -g restart false

function show_help
    echo "Usage: $argv[0] [--restart|-r] [--help|-h]"
    echo "  --restart, -r: Stop and remove existing container before starting"
    echo "  --help, -h: Show this help message"
end

# Parse command line arguments
for arg in $argv
    switch $arg
        case --restart -r
            set restart true
        case --help -h
            show_help
            exit 0
    end
end

if test "$restart" = "true"
    echo "Restarting JobSpy MCP server (stopping and removing existing containers)..."
    
    # Stop and remove existing containers if they exist
    for container_name in jobspy-mcp-server jobspy-mcp-server-instance
        if podman ps -a --filter "name=$container_name" | grep -q "$container_name"
            echo "Stopping container: $container_name"
            podman stop "$container_name" 2>/dev/null || true
            echo "Removing container: $container_name"
            podman rm "$container_name" 2>/dev/null || true
        end
    end
else
    echo "Starting JobSpy MCP server..."
end

# Check if any jobspy container is already running (only if not restarting)
if test "$restart" != "true"
    if podman ps --filter "name=jobspy-mcp-server" --filter "status=running" | grep -q jobspy-mcp-server
        echo "Container is already running."
    else if podman ps --filter "name=jobspy-mcp-server-instance" --filter "status=running" | grep -q jobspy-mcp-server-instance
        echo "Container is already running."
    else
        podman run --rm --name jobspy-mcp-server -p 9423:9423 jobspy-mcp-server
        echo "JobSpy MCP server started in background. Container name: jobspy-mcp-server"
    end
else
    podman run -d --name jobspy-mcp-server -p 9423:9423 jobspy-mcp-server
    echo "JobSpy MCP server started in background. Container name: jobspy-mcp-server"
end
