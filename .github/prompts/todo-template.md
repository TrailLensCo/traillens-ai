<!--
HOW TO USE THIS TEMPLATE (For Human Users):

1. Create a prompt file in .github/prompts/ with format: ${name}-prompt.md
   Example: api-auth-prompt.md, database-migration-prompt.md

2. Ask the AI assistant to convert it to a TODO list:
   "Convert the api-auth-prompt.md file to a TODO list using the todo-template.md"

3. AI will generate a detailed TODO file in .github/todo/${NAME}-TODO.md
   Example: API-AUTH-TODO.md, DATABASE-MIGRATION-TODO.md

4. Review the generated TODO list before starting implementation

WHAT GETS GENERATED:
- Phased implementation plan (Prerequisites → Implementation → Testing → Deployment)
- Each TODO with acceptance criteria, dependencies, affected files, risks, rollback plans
- Priority (P0-P3) and complexity (XS-XL) ratings
- Constitution compliance checklist
- Complete metadata and validation checklists

The content below is the template that guides AI assistants in generating these TODO lists.
-->

# Convert Prompt to TODO List

## Task Overview
Process a prompt markdown file and create a comprehensive TODO list in the `.github/todo/` directory following project constitution naming standards.

## Context
- Source: `.github/prompts/${name}-prompt.md`
- Target: `.github/todo/${NAME}-TODO.md` (ALL CAPS base name)
- Constitution requirement: TODO files MUST use ALL CAPS for base filename, end with `-TODO`, lowercase `.md` extension
- Example: `feature-implementation-prompt.md` → `FEATURE-IMPLEMENTATION-TODO.md`

## TODO File Output Structure

The generated TODO file MUST follow this structure:

```markdown
# [PROJECT NAME] TODO List

**Created:** YYYY-MM-DD
**Source Prompt:** `.github/prompts/${name}-prompt.md`
**Status:** 🔲 Not Started | 🔄 In Progress | ✅ Complete
**Project Phase:** Planning | Implementation | Testing | Deployment

## Overview
[2-3 sentence summary of what this TODO list accomplishes]

## Prerequisites
- [ ] Prerequisite item 1
- [ ] Prerequisite item 2

## Assumptions & Constraints
- Assumption 1
- Constraint 1

## Implementation Phases

### Phase 1: [Phase Name] (Setup & Prerequisites)
[TODOs for this phase]

### Phase 2: [Phase Name] (Core Implementation)
[TODOs for this phase]

### Phase 3: [Phase Name] (Testing & Validation)
[TODOs for this phase]

### Phase 4: [Phase Name] (Documentation & Deployment)
[TODOs for this phase]

## Risks & Mitigation
- **Risk:** [Description] | **Impact:** High/Medium/Low | **Mitigation:** [Strategy]

## Open Questions
- [ ] Question requiring clarification before implementation

## Constitution Compliance Checklist
- [ ] Python operations use `.venv/` virtual environment
- [ ] No shell-based file editing (sed/awk/cat)
- [ ] Artifactory URLs use JFrog CLI, not curl
- [ ] HTTP calls use requests/httpx, not subprocess
- [ ] README.md updates included
- [ ] All file paths use `pathlib.Path` or `os.path.join`
```

## TODO Item Structure Template

Each TODO item MUST follow this format:

```markdown
- [ ] **[Verb] [clear actionable description]** `(Priority: P0/P1/P2, Complexity: XS/S/M/L/XL, Owner: Role)`
  - **Acceptance Criteria:**
    - Criterion 1: Specific, measurable outcome
    - Criterion 2: Specific, measurable outcome
    - Criterion 3: Specific, measurable outcome
  - **Dependencies:** TODO #N, TODO #M (or "None")
  - **Affected Files:** 
    - `path/to/file1.ext` (create/modify/delete)
    - `path/to/file2.ext` (create/modify/delete)
  - **Testing Requirements:** Unit | Integration | E2E | Manual | Security
  - **Risks:** [High/Medium/Low] - [Description of risk and mitigation]
  - **Rollback Plan:** [What to do if this step fails]
  - **Notes:** [Any additional context, edge cases, or considerations]
```

### TODO Item Field Definitions

- **Priority Levels:**
  - `P0` - Critical/Blocking: Must complete before any other work
  - `P1` - High: Core functionality, complete in current phase
  - `P2` - Medium: Important but can be deferred if needed
  - `P3` - Low: Nice-to-have, optional enhancements

- **Complexity Scale:**
  - `XS` - < 30 min: Simple, straightforward change
  - `S` - 30min-2hrs: Single file/function, well-defined
  - `M` - 2-8hrs: Multiple files, some complexity
  - `L` - 1-3 days: Complex logic, multiple components
  - `XL` - 3+ days: Should be broken down into smaller tasks

- **Owner/Role:**
  - Backend, Frontend, DevOps, QA, DBA, Security, Documentation, etc.

- **Risk Levels:**
  - `High` - Could break existing functionality, security-critical, or complex
  - `Medium` - Some risk but contained/recoverable
  - `Low` - Minimal impact, easily reversible

### TODO Item Ordering Rules

1. **Dependency Order:** Items with no dependencies come first
2. **Risk-First for Critical Paths:** High-risk items early for de-risking
3. **Foundation-First:** Infrastructure/setup before features
4. **Parallel Tracks Identified:** Mark items that can run concurrently
5. **Validation After Implementation:** Testing TODOs follow implementation TODOs

## Complete TODO Item Examples

### Example 1: Backend Implementation
```markdown
- [ ] **Implement user authentication endpoint** `(Priority: P1, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - POST /api/auth/login accepts email/password in JSON body
    - Returns JWT token with 24h expiry on successful authentication
    - Returns 401 with error message on failed authentication
    - Rate limiting: Maximum 5 attempts per 15 minutes per IP
    - All authentication attempts logged with timestamp and IP
  - **Dependencies:** TODO #2 (Database schema), TODO #4 (JWT library setup)
  - **Affected Files:** 
    - `src/api/auth.py` (create)
    - `src/models/user.py` (modify - add password verification)
    - `tests/test_auth.py` (create)
    - `requirements.txt` (modify - add PyJWT)
  - **Testing Requirements:** Unit + Integration + Manual security testing
  - **Risks:** High - Security critical, needs peer security review before merge
  - **Rollback Plan:** Feature flag `ENABLE_AUTH_V2`, can disable if issues found
  - **Notes:** Use bcrypt for password hashing (already in dependencies), consult OWASP guidelines
```

### Example 2: Database Migration
```markdown
- [ ] **Create database migration for user_sessions table** `(Priority: P0, Complexity: S, Owner: DBA)`
  - **Acceptance Criteria:**
    - Migration script creates `user_sessions` table with correct schema
    - Adds indexes on `user_id` and `expires_at` columns
    - Migration is reversible (includes rollback script)
    - Tested on dev database without errors
  - **Dependencies:** None (blocking for TODO #5, #7, #11)
  - **Affected Files:**
    - `migrations/versions/2026_02_06_create_user_sessions.py` (create)
    - `src/models/session.py` (create)
  - **Testing Requirements:** Manual migration testing on dev environment
  - **Risks:** Medium - Database schema change, test thoroughly before production
  - **Rollback Plan:** Run down() migration to drop table
  - **Notes:** Ensure backup taken before production migration
```

### Example 3: Configuration
```markdown
- [ ] **Add environment configuration for JWT settings** `(Priority: P1, Complexity: XS, Owner: Backend)`
  - **Acceptance Criteria:**
    - JWT_SECRET_KEY added to .env.example with placeholder
    - JWT_EXPIRY_HOURS configurable (default: 24)
    - Configuration validation on app startup
    - Documentation updated in README.md
  - **Dependencies:** None
  - **Affected Files:**
    - `.env.example` (modify)
    - `src/config.py` (modify)
    - `README.md` (modify - add configuration section)
  - **Testing Requirements:** Unit tests for config validation
  - **Risks:** Low - Configuration only, no logic changes
  - **Rollback Plan:** Revert commits, no data impact
  - **Notes:** Never commit actual JWT_SECRET_KEY to repository
```

## Requirements

### Input Processing
1. Read the prompt file at `.github/prompts/${name}-prompt.md`
2. Analyze all sections: Task Overview, Context, Requirements, Expected Behavior, Additional Notes
3. Identify cross-cutting concerns: security, error handling, logging, monitoring
4. Extract file references, component names, and technical constraints
5. Note any Constitution rules that apply to the implementation

### TODO Generation
6. Create comprehensive TODO list with logical phase breakdown
7. Each TODO item MUST include ALL required fields:
   - Clear, actionable description with verb-first phrasing
   - Priority level (P0/P1/P2/P3) and complexity (XS/S/M/L/XL)
   - Owner/role assignment
   - Specific, measurable acceptance criteria (minimum 3)
   - Dependencies on other TODOs (or "None")
   - Complete list of affected files with action (create/modify/delete)
   - Testing requirements (types of tests needed)
   - Risk assessment with mitigation strategy
   - Rollback plan for failure scenarios
8. Break down any XL complexity items into smaller tasks (target: S-M complexity)
9. Order TODOs by dependencies and risk profile
10. Identify parallel execution opportunities

### File Output
11. Save the TODO list to `.github/todo/${NAME}-TODO.md` where `${NAME}` is the uppercase version of `${name}` with `-TODO` suffix
12. Follow the constitution TODO naming standard: ALL CAPS base name, `-TODO` suffix, `.md` extension
13. Include file header with metadata: creation date, source prompt, status, phase
14. Structure with clear phases: Prerequisites → Implementation → Testing → Deployment
15. Add Constitution compliance checklist at the end

## Expected Behavior

### Analysis Phase
- Prompt file read successfully from `.github/prompts/${name}-prompt.md`
- All requirements, context, and constraints extracted
- Technical approach validated against Constitution rules
- Edge cases and error scenarios identified
- File structure and component architecture understood

### TODO List Creation
- Comprehensive TODO list created with 4-phase structure minimum
- Each TODO item includes ALL required fields (no omissions)
- Complexity assessment complete (any XL items broken down)
- Dependencies mapped (no circular dependencies)
- Parallel execution tracks identified
- Risk assessment completed for each item

### Output Validation
- TODO file saved to `.github/todo/${NAME}-TODO.md`
- Naming convention validated: ALL CAPS base, `-TODO` suffix, `.md` extension
- File structure follows template: header → overview → phases → risks → questions → compliance
- All Constitution rules applicable to the task are noted
- README update requirements flagged if applicable

### Quality Checklist
Before presenting TODO list, verify:
- [ ] Every requirement from prompt captured in TODO items
- [ ] No orphaned dependencies (all referenced TODOs exist)
- [ ] All affected files identified with specific actions
- [ ] Edge cases addressed in acceptance criteria or notes
- [ ] Error handling and rollback plans included
- [ ] Acceptance criteria are specific and measurable
- [ ] No TODO violates Constitution rules
- [ ] Priority and complexity assigned to every item
- [ ] Testing requirements specified for each item
- [ ] Constitution compliance checklist included

## Additional Notes

### Implementation Readiness
- The TODO list must be immediately actionable (no ambiguity)
- Each TODO should be completable by a developer with standard project knowledge
- No TODO should require additional research to understand requirements
- All external dependencies (APIs, libraries, services) clearly identified

### Task Breakdown Guidelines
- Target complexity: Most items should be S-M (30min to 8hrs)
- If a task is XL (3+ days), MUST break down into smaller items
- Each TODO should have a single, clear completion state
- Prefer multiple small TODOs over one large TODO

### Constitution Compliance
- **Critical:** Flag any operations that might violate Constitution:
  - Shell scripts editing source files (PROHIBITED)
  - Python subprocess calls without justification
  - Direct curl/wget to Artifactory (use JFrog CLI)
  - Path concatenation without pathlib/os.path
  - Missing virtual environment usage
- Add Constitution compliance checklist to every TODO file
- Note README update requirement per Constitution workflow rules

### Edge Cases & Error Handling
- Consider null/empty inputs, boundary conditions, race conditions
- Include error scenarios in acceptance criteria
- Specify logging requirements for errors
- Define rollback procedures for risky operations

### Naming Convention Emphasis
- Input format: `${name}-prompt.md` (lowercase with hyphens)
- Output format: `${NAME}-TODO.md` (UPPERCASE with hyphens, `-TODO` suffix)
- Example transformations:
  - `database-migration-prompt.md` → `DATABASE-MIGRATION-TODO.md`
  - `api-auth-refactor-prompt.md` → `API-AUTH-REFACTOR-TODO.md`
  - `feature-user-profile-prompt.md` → `FEATURE-USER-PROFILE-TODO.md`

## Example Transformations
```
Input:  .github/prompts/api-refactor-prompt.md
Output: .github/todo/API-REFACTOR-TODO.md

Input:  .github/prompts/test-coverage-prompt.md
Output: .github/todo/TEST-COVERAGE-TODO.md

Input:  .github/prompts/feature-auth-prompt.md
Output: .github/todo/FEATURE-AUTH-TODO.md
```

## Instructions for AI Assistant

**CRITICAL Naming Rules**:
- Source file format: `${name}-prompt.md` (lowercase with hyphens)
- Target file format: `${NAME}-TODO.md` (UPPERCASE with hyphens, ending in `-TODO`)
- Example: `database-migration-prompt.md` → `DATABASE-MIGRATION-TODO.md`

**Process Workflow**:

### Step 1: Read & Analyze Prompt
1. Accept the `name` parameter (e.g., "database-migration")
2. Read the prompt file at `.github/prompts/${name}-prompt.md`
3. If file doesn't exist: report error, suggest creating it first
4. If file is malformed: request clarification on ambiguous sections
5. Extract all requirements, constraints, and expected outcomes
6. Identify technical approach and architectural components
7. Flag any Constitution rule conflicts immediately

### Step 2: Plan TODO Structure
8. Determine logical phase breakdown (typically 4-6 phases)
9. Identify prerequisite tasks (infrastructure, configuration, dependencies)
10. Map dependencies between tasks
11. Assess risks and complexity for each identified task
12. Group related tasks into phases
13. Identify tasks that can run in parallel

### Step 3: Generate TODO Items
14. For each task, create TODO item with ALL required fields:
    - Description: `**[Verb] [clear action]** (Priority: PX, Complexity: X, Owner: Role)`
    - Acceptance criteria: Minimum 3 specific, measurable outcomes
    - Dependencies: List TODO numbers or "None"
    - Affected files: Full paths with action (create/modify/delete)
    - Testing requirements: Specify test types needed
    - Risks: Level + description + mitigation
    - Rollback plan: What to do if step fails
    - Notes: Edge cases, considerations, Constitution compliance notes
15. Break down any XL complexity items into 2-4 smaller items
16. Number TODOs sequentially within each phase
17. Ensure dependency references are valid (no forward references to non-existent TODOs)

### Step 4: Add Metadata & Compliance
18. Create file header with creation date, source prompt, status, phase
19. Write 2-3 sentence overview summarizing the TODO list scope
20. Add prerequisites section if applicable
21. Document assumptions and constraints
22. Create risks & mitigation section
23. List open questions requiring clarification
24. Add Constitution compliance checklist specific to this project

### Step 5: Validate & Output
25. Run quality checklist (see Expected Behavior section)
26. Verify no Constitution violations
27. Check for orphaned dependencies
28. Confirm all files referenced are specific paths
29. Convert `name` to uppercase: `${name}` → `${NAME}`
30. Save TODO list to `.github/todo/${NAME}-TODO.md`
31. Present the TODO list for review **before starting any implementation**

### Step 6: Review & Iterate
32. Wait for user approval or feedback
33. If changes requested: update TODO file and re-present
34. Only mark as "implementation-ready" after explicit approval
35. **DO NOT begin implementation until TODO list is approved**

**Example Usage**:
```
/prompt-to-todo database-migration
→ Reads: .github/prompts/database-migration-prompt.md
→ Creates: .github/todo/DATABASE-MIGRATION-TODO.md
```

**Success Criteria**:

### Analysis Success
- [ ] Prompt file read and analyzed successfully
- [ ] All requirements and constraints extracted
- [ ] Technical approach understood and validated
- [ ] Constitution rules applicable to task identified
- [ ] Edge cases and error scenarios considered

### TODO Quality Success
- [ ] Every TODO includes ALL required fields (no omissions)
- [ ] Acceptance criteria are specific and measurable (no vague statements)
- [ ] Dependencies mapped correctly (no circular refs, no orphans)
- [ ] Complexity assessed (all XL items broken down)
- [ ] Risk levels assigned with mitigation strategies
- [ ] Rollback plans defined for risky operations
- [ ] All affected files listed with specific paths and actions
- [ ] Testing requirements specified for each item

### File Output Success
- [ ] File saved to `.github/todo/` with correct naming: `${NAME}-TODO.md` (ALL CAPS)
- [ ] Constitution naming standard followed (ALL CAPS base, `-TODO` suffix, `.md` extension)
- [ ] File structure follows template (header → phases → risks → compliance)
- [ ] Metadata complete (creation date, source, status, phase)
- [ ] Markdown formatting valid (checklist syntax, code blocks, links)

### Process Success
- [ ] TODO list presented for review (not just created silently)
- [ ] Quality checklist validated before presentation
- [ ] No implementation started until TODO list is approved
- [ ] User has opportunity to provide feedback and request changes

### Constitution Compliance Success
- [ ] No Constitution violations in planned implementation
- [ ] Constitution checklist included in output file
- [ ] README update noted if required
- [ ] Virtual environment usage specified for Python tasks
- [ ] Proper path construction methods specified
- [ ] Library-first approach validated (no reinventing wheels)

## Edge Case Handling

### Missing or Incomplete Prompts
- If prompt file doesn't exist: Report error with exact path checked, offer to create template
- If prompt missing sections: Request clarification, don't guess requirements
- If requirements conflict: Flag conflicts, request resolution before creating TODO

### Ambiguous Requirements
- If technical approach unclear: Provide 2-3 options in TODO notes, mark as "requires decision"
- If acceptance criteria unmeasurable: Flag in open questions, request clarification
- If scope too large: Suggest breaking into multiple prompt files / TODO lists

### Constitution Conflicts
- If prompt requests prohibited operation (e.g., shell-based file editing): 
  - Flag immediately
  - Suggest Constitution-compliant alternative
  - Mark as "requires exception approval" if no alternative
  - Include `# EXCEPTION:` comment guidance in TODO

### Cross-Cutting Concerns
- Security: Add security review step for auth, data handling, API endpoints
- Logging: Include logging requirements in acceptance criteria
- Monitoring: Add observability considerations for production features
- Performance: Flag potential bottlenecks in notes
- Documentation: Ensure README/API doc updates included

## Complete Example

### Input Prompt File: `.github/prompts/api-auth-prompt.md`
```markdown
# API Authentication Implementation

## Task Overview
Implement JWT-based authentication for the REST API with user login/logout endpoints.

## Requirements
- POST /api/auth/login endpoint (email/password → JWT token)
- POST /api/auth/logout endpoint (invalidate token)
- JWT tokens expire after 24 hours
- Rate limiting: 5 login attempts per 15 minutes per IP
- Password requirements: min 8 chars, 1 uppercase, 1 number
- All auth attempts logged

## Expected Behavior
- Users can authenticate and receive JWT token
- Token required for protected endpoints
- Invalid tokens return 401
- Expired tokens return 401
- Rate limiting prevents brute force attacks
```

### Output TODO File: `.github/todo/API-AUTH-TODO.md`
```markdown
# API Authentication Implementation TODO List

**Created:** 2026-02-06
**Source Prompt:** `.github/prompts/api-auth-prompt.md`
**Status:** 🔲 Not Started
**Project Phase:** Planning

## Overview
Implement JWT-based authentication system for REST API including user login/logout endpoints, token validation middleware, rate limiting, and comprehensive security logging.

## Prerequisites
- [ ] Python virtual environment configured (`.venv/`)
- [ ] Database schema includes users table with password_hash
- [ ] Redis available for rate limiting and token blacklist

## Assumptions & Constraints
- Using PyJWT library for token generation/validation
- bcrypt for password hashing (already in dependencies)
- Redis for distributed rate limiting and token blacklist
- PostgreSQL for user data storage

## Implementation Phases

### Phase 1: Setup & Configuration (Prerequisites)

- [ ] **Add JWT configuration to environment settings** `(Priority: P0, Complexity: XS, Owner: Backend)`
  - **Acceptance Criteria:**
    - JWT_SECRET_KEY added to .env.example with placeholder value
    - JWT_EXPIRY_HOURS configurable (default: 24)
    - JWT_ALGORITHM configurable (default: HS256)
    - Configuration validation on app startup raises error if missing
    - README.md updated with new environment variables
  - **Dependencies:** None
  - **Affected Files:**
    - `.env.example` (modify)
    - `src/config.py` (modify - add JWT settings class)
    - `README.md` (modify - add configuration section)
    - `tests/test_config.py` (modify - add JWT config tests)
  - **Testing Requirements:** Unit tests for config validation
  - **Risks:** Low - Configuration only, validated on startup
  - **Rollback Plan:** Revert commits, no data impact
  - **Notes:** Never commit actual JWT_SECRET_KEY to repository, use secrets manager in production

- [ ] **Install and configure PyJWT library** `(Priority: P0, Complexity: XS, Owner: Backend)`
  - **Acceptance Criteria:**
    - PyJWT added to requirements.txt with version pinning (^2.8.0)
    - Library installed in virtual environment using pip
    - Import test passes (can import jwt module)
    - Version compatibility verified with Python 3.11+
  - **Dependencies:** None
  - **Affected Files:**
    - `requirements.txt` (modify - add PyJWT==2.8.0)
  - **Testing Requirements:** Manual import verification
  - **Risks:** Low - Well-maintained library, stable API
  - **Rollback Plan:** Remove from requirements.txt
  - **Notes:** Use Artifactory mirror for pip install per Constitution

### Phase 2: Core Implementation

- [ ] **Implement JWT token generation utility** `(Priority: P1, Complexity: S, Owner: Backend)`
  - **Acceptance Criteria:**
    - Function `generate_jwt_token(user_id: int) -> str` created
    - Token includes user_id, issued_at, expires_at claims
    - Token expiry matches JWT_EXPIRY_HOURS configuration
    - Function raises ValueError for invalid user_id
    - Token structure validated with jwt.decode
  - **Dependencies:** TODO #1 (JWT configuration)
  - **Affected Files:**
    - `src/auth/jwt_utils.py` (create)
    - `tests/unit/test_jwt_utils.py` (create)
  - **Testing Requirements:** Unit tests (happy path + error cases)
  - **Risks:** Medium - Security critical, needs review
  - **Rollback Plan:** Not user-facing until endpoint integrated
  - **Notes:** Follow OWASP JWT best practices, avoid sensitive data in token payload

- [ ] **Implement POST /api/auth/login endpoint** `(Priority: P1, Complexity: M, Owner: Backend)`
  - **Acceptance Criteria:**
    - Accepts JSON body with email and password fields
    - Validates password meets requirements (8+ chars, 1 upper, 1 number)
    - Returns 200 with {"token": "<JWT>"} on success
    - Returns 401 with {"error": "Invalid credentials"} on failure
    - Returns 400 with {"error": "Validation error"} for malformed input
    - Password verified using bcrypt compare
    - All attempts logged with timestamp, email, IP, success/failure
  - **Dependencies:** TODO #3 (JWT generation), TODO #5 (rate limiting)
  - **Affected Files:**
    - `src/api/routes/auth.py` (create)
    - `src/models/user.py` (modify - add verify_password method)
    - `tests/integration/test_auth_endpoints.py` (create)
  - **Testing Requirements:** Integration + Manual security testing
  - **Risks:** High - Security critical, authentication endpoint
  - **Rollback Plan:** Feature flag ENABLE_JWT_AUTH, can disable if issues
  - **Notes:** Use constant-time comparison for email lookup to prevent timing attacks

[... continues with Phase 3: Testing & Validation, Phase 4: Documentation & Deployment]

## Risks & Mitigation
- **Risk:** JWT secret key leakage | **Impact:** Critical | **Mitigation:** Use secrets manager, rotate keys regularly, never commit to git
- **Risk:** Token replay attacks | **Impact:** High | **Mitigation:** Implement token blacklist on logout, short expiry times
- **Risk:** Brute force attacks | **Impact:** High | **Mitigation:** Rate limiting (5 attempts/15min), account lockout after 10 failures

## Open Questions
- [ ] Should we implement refresh tokens for longer sessions?
- [ ] Do we need OAuth2 provider support (Google, GitHub)?
- [ ] What's the account lockout policy after repeated failures?

## Constitution Compliance Checklist
- [ ] Python operations use `.venv/` virtual environment
- [ ] PyJWT installed via Artifactory mirror, not public PyPI
- [ ] No shell-based file editing (sed/awk/cat)
- [ ] HTTP calls use requests library (rate limiting, logging)
- [ ] README.md updates included (TODO #1, TODO #12)
- [ ] All file paths use `pathlib.Path` in Python code
- [ ] No subprocess calls to curl/wget
- [ ] Library-first approach (PyJWT, bcrypt - no custom crypto)
```
