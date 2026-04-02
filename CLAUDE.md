# AGENTS.md - JobSpy MCP Server

Instructions for agentic coding agents working on the JobSpy MCP Server codebase.

## Commands

**Use pnpm** - Required due to symlink preservation for nested node_modules (critical for jobspy dependency)

### Development
- `pnpm start` - Start production server
- `pnpm dev` - Start with nodemon auto-reload
- `pnpm lint` / `pnpm lint:fix` - Lint and auto-fix

### Testing
- `tests/api.http` - 21 HTTP client test scenarios for Neovim (kulala.nvim, rest.nvim)
- Run with `:KulalaRun` / `:KulalaRunAll`

### Container (Podman)
- `./start-jobspy-mcp.zsh` - Start container
- `./start-jobspy-mcp.zsh --restart` - Restart (stop/remove/start)
- Manual: `podman build -t jobspy-mcp-server .`

---

## Code Style

### Formatting (enforced by ESLint)
- 2 spaces, single quotes, semicolons always
- Trailing commas required for multiline
- Max 200 chars per line, Unix line breaks

### Naming
- Variables/functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case.js`
- Properties: `camelCase` (match API responses)

### Imports
```
// Order: built-ins → external libs → local modules
import fs from 'fs';
import { z } from 'zod';
import { searchParams } from '../schemas/searchParamsSchema.js';
```

### Error Handling
- Return error objects, never throw (prevents container crashes)
- Use winston logger: `logger.error()`, `logger.info()`
- Use Zod schemas for validation in `src/schemas/`

```javascript
// Good
try {
  const result = riskyOperation();
  return { success: true, data: result };
} catch (error) {
  logger.error('Operation failed', { error: error.message });
  return { error: true, message: error.message };
}
```

### Variables
- Use `const` by default, `let` only for reassignment
- Never use `var`
- Prefer arrow functions for callbacks

---

## API Parameters (snake_case)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_names` | string | `indeed` | indeed,linkedin,zip_recruiter,glassdoor,google |
| `search_term` | string | `software engineer` | Job search term |
| `location` | string | `San Francisco, CA` | Search location |
| `results_wanted` | int | `20` | Number of results |
| `hours_old` | int | `72` | Max job age in hours |
| `country_indeed` | string | `USA` | Country for Indeed |
| `is_remote` | bool | `false` | Remote jobs only |
| `job_type` | string | - | fulltime/parttime/internship/contract |
| `distance` | int | `50` | Search radius (miles) |
| `easy_apply` | bool | `false` | Easy apply filter |
| `format` | string | `json` | json/csv output |
| `offset` | int | `0` | Pagination offset |

### Parameter Pipeline
1. **Reception**: `POST /api` with `{"method": "search_jobs", "params": {...}}`
2. **Conversion**: snake_case → camelCase (`search_term` → `searchTerm`)
3. **Mapping**: `location` → `country_indeed` when not explicitly set
4. **Validation**: Zod schemas with defaults and transforms
5. **Command Building**: camelCase → Python args (`isRemote: true` → `--is_remote True`)
6. **Execution**: `python /app/jobspy/main.py [args]`

---

## MCP Integration

- **Dual Transport**: MCP protocol + REST API (`POST /api`)
- **SSE**: Real-time progress for long searches (`GET /sse`)
- **Tool Registration**: `search_jobs` tool registered with MCP server

---

## Directory Structure

```
src/
├── tools/      # MCP tool implementations
├── schemas/    # Zod validation schemas
├── prompts/    # MCP prompt definitions
tests/
├── api.http    # HTTP client tests
```

---

## Key Patterns

- **Validation**: Always validate inputs with Zod in `src/schemas/`
- **Logging**: Use winston logger, include context metadata
- **Errors**: Return error objects, log with winston
- **Testing**: Add test cases to `tests/api.http` for new endpoints
