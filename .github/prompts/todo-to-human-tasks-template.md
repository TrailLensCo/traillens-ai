# Convert TODO to Human-Readable Task List

## Task Overview
Process a TODO markdown file and create a simplified, human-readable task list suitable for individuals with limited programming knowledge. The output should use plain language, avoid technical jargon, and provide clear step-by-step instructions.

## Context
- Source: `.github/todo/${NAME}-TODO.md` (TODO file with ALL CAPS base name)
- Target: `.github/tasks/${name}-tasks.md` (human-readable tasks in lowercase)
- Audience: Team members with limited programming knowledge
- Goal: Make technical tasks accessible and actionable for non-technical contributors

## Requirements
1. Read the TODO file at `.github/todo/${NAME}-TODO.md`
2. Analyze each TODO item and its technical requirements
3. Translate technical terminology into plain language
4. Break down complex technical steps into simple, sequential actions
5. Provide context and explanations for "why" each task matters
6. Save the human-readable task list to `.github/tasks/${name}-tasks.md`
7. Each task item must include:
   - Plain language description (avoid jargon)
   - Clear step-by-step instructions
   - Visual or file location guidance (e.g., "Open the file called...")
   - Expected outcome (what success looks like)
   - Who to ask for help if stuck
   - Estimated time/difficulty level

## Expected Behavior
- TODO file read and technical requirements understood
- Technical jargon translated to accessible language
- Complex tasks broken into simple, sequential steps
- Task list saved to `.github/tasks/${name}-tasks.md`
- Task list includes:
  - Overview in plain language
  - Numbered task items with simple descriptions
  - Step-by-step instructions for each task
  - Screenshots or diagrams suggestions where helpful
  - "Success looks like..." statements
  - Resources and help contacts

## Translation Guidelines

### Technical to Plain Language Examples
- "Document Terraform usage" → "Write instructions for how to use the infrastructure automation tool"
- "Document RBAC configuration" → "Write a guide explaining who has access to what in the system"
- "Add architecture diagram" → "Create a visual diagram showing how the different parts connect"
- "Update README" → "Update the project introduction document"
- "Configure namespace" → "Set up the project workspace"

### Breaking Down Technical Tasks
Instead of: "Document Terraform usage"
Write:
1. Open the README file in the project folder
2. Add a new section called "How to Use Infrastructure Tools"
3. Write 3-5 sentences explaining what Terraform does (it helps set up servers automatically)
4. List the basic commands someone would type to get started
5. Add a link to the official Terraform beginner guide

## Format Template

```markdown
# [Project Name] - Tasks for [Feature/Area]

## What This Is About
[2-3 sentence overview in plain language about what we're trying to accomplish]

## Task List

### Task 1: [Simple Task Name]
**What you'll do**: [Plain language description]

**Why this matters**: [Explain the purpose]

**Steps**:
1. [Simple action with file location]
2. [Next simple action]
3. [Continue...]

**Success looks like**: [What the end result should be]

**Time estimate**: [Easy/Medium/Needs help - X minutes/hours]

**Need help?**: Contact [person/team]

---

[Repeat for each task]
```

## Additional Notes
- Use conversational, friendly tone
- Avoid acronyms without explanation
- Provide file paths and locations clearly
- Suggest visual aids where possible (screenshots, diagrams)
- Include "what could go wrong" notes for tricky parts
- Add encouragement and reassurance
- Link to learning resources for unfamiliar concepts
- Make tasks feel achievable and not overwhelming

## Example Transformation

### Input (Technical TODO):
```
- [ ] Document RBAC configuration
  - Acceptance Criteria: Complete documentation of role-based access control
```

### Output (Human-Readable Task):
```
### Task 3: Write a Guide About System Permissions

**What you'll do**: Create a document that explains who can access what parts of the system

**Why this matters**: New team members need to understand what permissions they have and how to request access to different areas.

**Steps**:
1. Open the file called `README.md` in the main project folder
2. Add a new section with the heading "System Permissions and Access"
3. Write a short paragraph (3-5 sentences) explaining that the system has different permission levels
4. Create a simple table with three columns: "Role Name", "What They Can Do", "Example Person"
5. Fill in the table with the different permission levels (you can find these in the `rbac-config.yaml` file)
6. Add a sentence at the end telling people how to request access changes (usually contact the DevOps team)

**Success looks like**: Someone new to the project can read your section and understand what access they have and how permissions work.

**Time estimate**: Medium difficulty - about 30-45 minutes

**Need help?**: Ask the DevOps team or check the official Kubernetes RBAC documentation
```

## Instructions for AI Assistant

**Process**:
1. Accept the `name` parameter (e.g., "k8s-infra")
2. Read the TODO file at `.github/todo/${NAME}-TODO.md` (uppercase version)
3. Analyze each TODO item and identify technical terminology
4. Translate technical concepts to plain language
5. Break complex tasks into simple, sequential steps
6. Add context, explanations, and encouragement
7. Create human-readable task file at `.github/tasks/${name}-tasks.md` (lowercase)
8. Present the task list for review

**Example Usage**:
```
/todo-to-human-tasks k8s-infra
→ Reads: .github/todo/K8S-INFRA-TODO.md
→ Creates: .github/tasks/k8s-infra-tasks.md
```

**Success Criteria**:
- [ ] TODO file read and analyzed successfully
- [ ] Technical jargon translated to accessible language
- [ ] Complex tasks broken into simple steps
- [ ] File saved to `.github/tasks/${name}-tasks.md`
- [ ] Task list uses conversational, friendly tone
- [ ] Each task includes "what", "why", "how", and "success"
- [ ] Appropriate help resources and contacts included
- [ ] Task list reviewed and approved before sharing with team
