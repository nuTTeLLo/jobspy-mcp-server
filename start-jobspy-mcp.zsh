#!/bin/zsh

# Start the JobSpy MCP server container with SSE enabled in the background

# Parse command line arguments
RESTART=false
for arg in "$@"; do
  case $arg in
    --restart|-r)
      RESTART=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--restart|-r] [--help|-h]"
      echo "  --restart, -r: Stop and remove existing container before starting"
      echo "  --help, -h: Show this help message"
      exit 0
      ;;
  esac
done

if $RESTART; then
  echo "Restarting JobSpy MCP server (stopping and removing existing containers)..."

  # Stop and remove existing containers if they exist
  for container_name in "jobspy-mcp-server" "jobspy-mcp-server-instance"; do
    if podman ps -a --filter "name=$container_name" | grep -q "$container_name"; then
      echo "Stopping container: $container_name"
      podman stop "$container_name" 2>/dev/null || true
      echo "Removing container: $container_name"
      podman rm "$container_name" 2>/dev/null || true
    fi
  done
else
  echo "Starting JobSpy MCP server..."
fi

# Check if any jobspy container is already running (only if not restarting)
if ! $RESTART && (podman ps --filter "name=jobspy-mcp-server" --filter "status=running" | grep -q jobspy-mcp-server || podman ps --filter "name=jobspy-mcp-server-instance" --filter "status=running" | grep -q jobspy-mcp-server-instance); then
  echo "Container is already running."
else
  podman run -d --name jobspy-mcp-server -p 9423:9423 jobspy-mcp-server
  echo "JobSpy MCP server started in background. Container name: jobspy-mcp-server"
fi
