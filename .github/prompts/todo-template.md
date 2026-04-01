# Convert Prompt to TODO List

## Task Overview
Process a prompt markdown file and create a comprehensive TODO list in the `.github/todo/` directory following TrailLens constitution naming standards.

## Context
- Source: `.github/prompts/${name}-prompt.md`
- Target: `.github/todo/${NAME}-TODO.md` (ALL CAPS base name)
- Constitution requirement: TODO files MUST use ALL CAPS for base filename, end with `-TODO`, lowercase `.md` extension
- Example: `feature-implementation-prompt.md` → `FEATURE-IMPLEMENTATION-TODO.md`

## Requirements
1. Read the prompt file at `.github/prompts/${name}-prompt.md`
2. Analyze the task requirements, context, and expected behavior
3. Create a detailed TODO list breaking down the work into actionable steps
4. Save the TODO list to `.github/todo/${NAME}-TODO.md` where `${NAME}` is the uppercase version of `${name}` with `-TODO` suffix
5. Each TODO item must have:
   - Clear, actionable description
   - Acceptance criteria
   - Dependencies on other TODOs if applicable
   - File paths or components affected
6. Follow the constitution TODO naming standard: ALL CAPS base name, `-TODO` suffix, `.md` extension

## Expected Behavior
- Prompt file analyzed and understood
- Comprehensive TODO list created with logical step breakdown
- TODO file saved to `.github/todo/${NAME}-TODO.md`
- TODO list must include:
  - Overview/summary of the task
  - Numbered TODO items with descriptions
  - Dependencies between items
  - Acceptance criteria for each item
  - Estimated complexity or notes where helpful

## Additional Notes
- The TODO list should be implementation-ready
- Break complex tasks into smaller, manageable steps
- Consider edge cases and error handling in the TODO items
- Reference relevant files and components
- Follow TrailLens constitution standards for all file operations
- The naming convention is critical: `database-migration` → `DATABASE-MIGRATION-TODO.md`

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

**Process**:

1. Accept the `name` parameter (e.g., "database-migration")
2. Read the prompt file at `.github/prompts/${name}-prompt.md`
3. Analyze all sections: Task Overview, Context, Requirements, Expected Behavior
4. Create a comprehensive TODO list with:
   - Task summary at the top
   - Numbered items (use markdown checklist format)
   - Clear descriptions and acceptance criteria
   - File references and component names
   - Dependencies noted where applicable
5. Convert `name` to uppercase: `${name}` → `${NAME}`
6. Save TODO list to `.github/todo/${NAME}-TODO.md`
7. Present the TODO list for review before implementation
8. If the `.github/todo/${NAME}-TODO.md` already exists, it should be read and updated
9. Any unknowns should be listed in a Questions section rather than making assumptions

**Example Usage**:
```
/prompt-to-todo database-migration
→ Reads: .github/prompts/database-migration-prompt.md
→ Creates: .github/todo/DATABASE-MIGRATION-TODO.md
```

**Success Criteria**:
- [ ] Prompt file read and analyzed successfully
- [ ] TODO list created with clear, actionable items
- [ ] File saved to `.github/todo/` with correct naming: `${NAME}-TODO.md` (ALL CAPS)
- [ ] Constitution naming standard followed (ALL CAPS base, `-TODO` suffix, `.md` extension)
- [ ] TODO list presented for review
- [ ] No implementation started until TODO list is approved
