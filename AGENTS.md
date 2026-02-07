# AGENTS.md - JobSpy MCP Server

This file contains instructions for agentic coding agents working on the JobSpy MCP Server codebase.

## Build, Lint, and Test Commands

### Development Commands
- `npm start` - Start the production server
- `npm run dev` - Start development server with auto-reload (nodemon)
- `npm run lint` - Run ESLint on source files
- `npm run lint:fix` - Auto-fix ESLint issues
- `npm test` - Run tests (currently not implemented - placeholder)

### Single Test Execution
Tests are not currently configured with a test runner. To run individual test files:
```bash
# Run a specific test file (requires test runner setup)
node tests/jobSchema.test.js
```

### Container Commands
- `task build` - Build the jobspy container (requires task runner)
- `task start` - Build container and start server (requires task runner)
- `./start-jobspy-mcp.fish` - Start the server container using Podman (Fish shell)
- `./start-jobspy-mcp.fish --restart` - Restart container (stop/remove/start)
- `./start-jobspy-mcp.zsh` - Start the server container using Podman (Zsh shell)
- `./start-jobspy-mcp.zsh --restart` - Restart container (stop/remove/start)
- Manual Podman build: `podman build -t jobspy-mcp-server .`
- Container name: `jobspy-mcp-server`

### Overall Application
The MCP server is part of the larger Job Tracker application. Use the root startup script to start all services together:

```bash
# From project root (Fish shell)
./startup.fish
./startup.fish --restart  # Force rebuild all services

# Or using Zsh
./startup.zsh
./startup.zsh --restart  # Force rebuild all services
```

### Environment Setup
- Node.js 16+
- Python 3.6+ (for jobspy dependency)
- Copy `.env` file and configure environment variables

## Code Style Guidelines

### Language and Modules
- **ES6 Modules**: Use `import`/`export` syntax, no CommonJS
- **File Extensions**: Use `.js` for JavaScript files
- **Type**: `"module"` in package.json enables ES6 modules

### Formatting
- **Indentation**: 2 spaces (no tabs)
- **Quotes**: Single quotes for strings (`'string'`)
- **Semicolons**: Always use semicolons
- **Line Length**: Maximum 200 characters per line
- **Trailing Commas**: Required for multiline arrays/objects
- **Line Breaks**: Unix style (LF)

### Naming Conventions
- **Variables/Functions**: camelCase (`searchJobsHandler`, `validateParams`)
- **Constants**: UPPER_SNAKE_CASE for true constants
- **Files**: kebab-case (`search-jobs.js`, `job-schema.js`)
- **Classes**: PascalCase (if any)
- **Properties**: camelCase, consistent with API responses

### Imports and Exports
- **Import Order**: Group by type (built-ins, external libs, local modules)
- **Import Style**: Named imports preferred over default
- **Export Style**: Named exports for utilities, default for main classes/functions
- **Extensions**: Omit `.js` extensions in import statements

```javascript
// Good
import logger from '../logger.js';
import { z } from 'zod';
import { searchParams } from '../schemas/searchParamsSchema.js';

// Avoid
import * as utils from './utils.js';
```

### Variables and Declarations
- **const/let**: Use `const` by default, `let` only when reassignment needed
- **var**: Never use `var`
- **Destructuring**: Use when accessing multiple properties
- **Arrow Functions**: Preferred for callbacks and short functions

### Error Handling
- **Try/Catch**: Use try/catch blocks for operations that may fail
- **Error Objects**: Return error objects instead of throwing (prevents container crashes)
- **Logging**: Use winston logger for all logging, not console methods
- **Validation**: Use Zod schemas for input validation

```javascript
// Good - return error object
try {
  const result = riskyOperation();
  return { success: true, data: result };
} catch (error) {
  logger.error('Operation failed', { error: error.message });
  return { error: true, message: error.message };
}

// Avoid - throwing exceptions
throw new Error('Something went wrong');
```

### Data Transformation
- **change-case-object**: Use for converting between naming conventions
- **Date Handling**: Convert dates to ISO 8601 format
- **Type Coercion**: Use Zod transforms for safe type conversion

### Logging
- **Logger**: Import and use the custom winston logger
- **Log Levels**: error, warn, info, debug
- **Metadata**: Include relevant context in log messages
- **Console**: Use console.log for detailed debugging during development
- **Parameter Processing**: Comprehensive logging of each step in the parameter pipeline

```javascript
// Good
logger.info('Starting job search', { params, userId });

// Development debugging
console.log('Parameter conversion:', JSON.stringify(params, null, 2));
```

### Validation and Schemas
- **Zod**: Use for all input validation and type checking
- **Schema Location**: Keep schemas in `src/schemas/` directory
- **Error Messages**: Provide descriptive validation error messages
- **Defaults**: Set sensible defaults in schemas
- **Transforms**: Use Zod transforms for data normalization

### API Design
- **RESTful**: Follow REST principles for HTTP endpoints
- **JSON**: Use JSON for request/response bodies
- **Status Codes**: Use appropriate HTTP status codes
- **Error Responses**: Consistent error response format
- **CORS**: Enable CORS for web client access

### Parameter Processing Pipeline

The JobSpy MCP Server processes API parameters through a comprehensive pipeline:

#### 1. **Request Reception**
- API endpoint: `POST /api`
- Accepts JSON payload: `{"method": "search_jobs", "params": {...}}`
- Extracts parameters from `req.body.params`

#### 2. **Parameter Conversion**
- Converts snake_case API parameters to camelCase internally
- Examples: `search_term` → `searchTerm`, `site_name` → `siteName`

#### 3. **Automatic Mapping**
- Maps `location` to `country_indeed` when `country_indeed` is not explicitly provided
- Example: `location: "Australia"` → `countryIndeed: "Australia"`

#### 4. **Validation & Defaults**
- Uses Zod schemas for parameter validation
- Applies default values for missing optional parameters
- Transforms values (e.g., string booleans, enum validation)

#### 5. **Command Building**
- Converts validated parameters to Python command arguments
- Examples:
  - `siteName: "indeed"` → `--site_name "indeed"`
  - `isRemote: true` → `--is_remote True`
  - `resultsWanted: 10` → `--results_wanted 10`

#### 6. **Python Execution**
- Calls: `python /app/jobspy/main.py [args]`
- Captures JSON output from jobspy library
- Returns formatted job results

### MCP Integration

- **Dual Transport**: Supports both MCP protocol and REST API
- **Tool Registration**: Registers `search_jobs` tool with MCP server
- **Progress Updates**: SSE transport provides real-time progress for long searches
- **Error Handling**: Returns structured error responses for both transports

### Container Management

- **Build Commands**: `podman build -t jobspy-mcp-server .`
- **Start Script**: `./start-jobspy-mcp.zsh` (Podman-based)
- **Restart Option**: `./start-jobspy-mcp.zsh --restart` (stops/removes/restarts container)
- **Container Name**: `jobspy-mcp-server`
- **Environment**: Node.js + Python container with jobspy dependencies

### Code Organization
- **Directory Structure**:
  - `src/` - Source code
  - `src/tools/` - MCP tool implementations
  - `src/schemas/` - Zod validation schemas
  - `src/prompts/` - MCP prompt definitions
  - `tests/` - Test files
- **Single Responsibility**: Each file/module should have one clear purpose
- **Comments**: Add JSDoc comments for public functions and complex logic
- **Constants**: Define magic numbers/strings as named constants

### Security Best Practices
- **Input Validation**: Always validate and sanitize inputs
- **Secrets**: Never log or commit API keys, tokens, or credentials
- **Error Messages**: Don't expose sensitive information in error messages
- **HTTPS**: Use HTTPS in production environments

### Testing
- **Test Files**: Place in `tests/` directory with `.test.js` extension
- **Test Structure**: Arrange, Act, Assert pattern
- **Mocking**: Mock external dependencies when needed
- **Coverage**: Aim for good test coverage of critical paths

### Performance
- **Async/Await**: Use for asynchronous operations
- **Memory**: Be mindful of memory usage with large datasets
- **Timeouts**: Set appropriate timeouts for external API calls
- **Streaming**: Consider streaming for large responses

### MCP-Specific Guidelines
- **Tool Registration**: Register tools with the MCP server using proper schemas
- **Progress Updates**: Implement progress reporting for long-running operations
- **Error Handling**: Handle MCP protocol errors gracefully
- **SSE Transport**: Support Server-Sent Events for real-time updates

### Environment Variables
- **Naming**: Use `JOBSPY_*` prefix for project-specific variables
- **Documentation**: Document all environment variables in README
- **Defaults**: Provide sensible defaults for all configuration
- **Validation**: Validate environment configuration on startup

### Dependencies
- **Package Management**: Use npm/pnpm for Node.js dependencies
- **Version Pinning**: Use specific versions in package.json
- **Security**: Regularly audit dependencies for vulnerabilities
- **Minimal**: Only include necessary dependencies

### Git Workflow
- **Commits**: Write clear, descriptive commit messages
- **Branches**: Use feature branches for development
- **PRs**: Create pull requests for code review
- **Linting**: Ensure code passes linting before committing

### Container
- **Podman**: Uses Podman for containerization (Linux/macOS)
- **Multi-stage**: Consider multi-stage builds for optimization
- **Security**: Use non-root user in containers
- **Volumes**: Mount volumes for persistent data if needed
- **Networking**: Expose appropriate ports and configure networking

### Key Features & Fixes

- **Parameter Processing**: Comprehensive pipeline converting snake_case API params to camelCase, with automatic location→country_indeed mapping
- **Zod Validation**: Full schema validation with sensible defaults and type coercion
- **Boolean Parameters**: Proper handling of boolean values (True/False for Python compatibility)
- **Command Building**: Automatic conversion of validated parameters to Python command arguments
- **Container Management**: Start script with restart functionality for easy deployment
- **Comprehensive Logging**: Step-by-step logging of parameter processing for debugging
- **MCP Integration**: Dual support for MCP protocol and REST API endpoints</content>
<parameter name="filePath">/Users/adrian/devenv/jobspy-mcp-server/AGENTS.md