<!--
═══════════════════════════════════════════════════════════════════════════════
HOW TO USE THIS TEMPLATE (For Human Users)
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
This is your starting point for capturing raw, unstructured ideas before they
become organized prompts. Just dump your thoughts here without worrying about
structure or completeness.

WHEN TO USE THIS:
- You have a rough idea but haven't thought through all the details yet
- You're brainstorming and want to capture thoughts quickly
- You know WHAT you want but not HOW or all the specifics
- You want to start simple and add structure later

WORKFLOW:
  Raw Idea → [This File] → plan-template.md → AI Processes → TODO List

  Step 1: Fill out this template (quick brain dump)
  Step 2: Use plan-template.md to organize and structure it
  Step 3: Ask AI to convert to TODO list

STEP-BY-STEP:

1. COPY THIS TEMPLATE
   Save as: .github/prompts/${name}-prompt.md
   Example: api-auth-prompt.md, user-dashboard-prompt.md

2. FILL IN THE UNSTRUCTURED PROMPT SECTION
   - Write naturally, as if explaining to a colleague
   - Don't worry about being complete or perfectly organized
   - Include whatever details you know, skip what you don't
   - Bullet points, paragraphs, whatever works for you

3. ADD OPTIONAL DETAILS (if known)
   - Goals: What are you trying to achieve?
   - Known Files: Which files will probably be affected?
   - Tech Stack: What tools/libraries/frameworks are involved?
   - Concerns: What are you worried about?

4. SAVE THE FILE
   Location: .github/prompts/${name}-prompt.md

5. NEXT STEP: ORGANIZE IT
   Option A: Ask AI: "Help me organize ${name}-prompt.md using plan-template.d"

6. THEN: CONVERT TO TODO
   After organizing with plan-template: "Convert the ${name}-prompt.md to a TODO list using todo-template.md"

EXAMPLE:

  Before (raw idea): "Need to add login"

  After using this template:
  ┌─ File: .github/prompts/api-auth-prompt.md
  │
  ├─ Unstructured Prompt:
  │  "We need to add authentication to the API. Right now anyone can access
  │   all endpoints. Want JWT tokens. Users should POST email/password and
  │   get back a token. Need rate limiting so people don't brute force it.
  │   Should probably log attempts too."
  │
  ├─ Goals: Secure the API, prevent unauthorized access
  ├─ Known Files: src/api/ somewhere
  ├─ Tech Stack: Flask, probably PyJWT
  └─ Concerns: Security is critical, don't want to mess it up

  Next: Use plan-template.md to structure requirements, add acceptance criteria, etc.

TIPS:

✓ DO:
  - Write naturally and conversationally
  - Include examples if they help explain
  - Mention any files/components you know about
  - Note things you're unsure about
  - Add links to related issues/docs if available

✗ DON'T:
  - Stress about perfect organization (that's for plan-template)
  - Skip this because "it's too simple" - capture helps!
  - Write code (describe what you want, not how to implement)
  - Worry about completeness - add what you know now

═══════════════════════════════════════════════════════════════════════════════
The template starts below. Fill it out naturally, don't overthink it.
═══════════════════════════════════════════════════════════════════════════════
-->

# Unstructured Prompt Template

## Unstructured Prompt
<!--
This is the core section - just explain what you want in your own words.
Write as if you're explaining the idea to a teammate over coffee.
No specific format required, just capture your thoughts.

Good examples:
- "Need to add a user profile page where people can update their info..."
- "The current search is too slow when we have more than 1000 items..."
- "Want to migrate from SQLite to PostgreSQL because..."

Include whatever you know:
- What problem you're solving
- Why it matters
- What you're trying to accomplish
- Any ideas you have about approach
- Examples of what it should do
- Things you know won't work
-->

The ai project currently has a podman container set that similates what we want to run in aws. This includes litellm, postgress, and redis. We also want an instance of opencode server. Because we want to keep the costs low, we would like to run the services on the bare metal and not through containers. Containers would be ideal, but the overhead to have the podman or docker running is more than what we need. We will give up some easy of maintainabiltiy for reduced costs for running the server.

The ai project already has a podman containerized system running and can be used for reference for config files.

The AWs EC2 instance must have a minimum required ram to support the applications. It should have 2 CPU's. The instance should also have sufficient storage (at least 30GB). We need to analyze the costs of this instance running 24/7 and from 7am to 12 midnight. We want an eventbridge service to be available to autoshutdown the system overnight when it will not be in use. The services on the system must use ngxinx as a reverse proxy into the services into the system, much like the container has now, but running on post 8080 which we expose to the internet at the url of https://ai.traillenshq.com. Use the nginx config in the podman-compose file from the existing podman setup for config examples.

## Quick Capture (Optional)
<!-- Use these optional fields to quickly jot down key information if you know it -->

**What I'm trying to achieve:**
- Make LiteLLM available opencode TU and IDE, opencode mobile, and the continue.dev IDE running on my laptop from anywhere to give access to all the models currently configured in Pulumi
- use pulumi to update and maintain the EC2 instance and DNS entries on route 53
- A single public elastic IP allocated to the EC2 instance.
- AWS Systems Manager session setup on the EC2 instance for shell access
- A security group configured to allow necessary inbound/outbound traffic for LiteLLM and other services
- Create a system in AWS to manage our Agent Orchestration
- there must be a create script or other mechanism to provision the server with all the software installed and configured.

**Things I'm not sure about yet:**
- How to securely expose LiteLLM endpoints across multiple clients without exposing credentials or API keys
- Cost. We need to analyze the code of running the system and its services based on AWS documentation. Do not make shit up.

## Notes & Context (Optional)
<!-- Any other thoughts, background info, or context that might be helpful -->

Use the AskUserQuestion tool to ask questions about ambigutities about the request. Do not make shit up. Research and review the existing codebase, documentation, and similar implementations as well as reviewing documentation on the internet.

---

## Next Steps

Once you've filled this out:

1. **Organize it** using `plan-template.md`:
   - Transfer your unstructured prompt to the structured sections
   - Fill out Requirements, Context, Expected Behavior with more detail
   - Add specific acceptance criteria and constraints

2. **OR ask AI to help organize:**
   - Command: "Help me organize [filename]-prompt.md using plan-template"
   - AI will help structure your thoughts into a detailed prompt

3. **Then convert to TODO list:**
   - Command: "Convert the [filename]-prompt.md to a TODO list"
   - AI will generate comprehensive TODO in `.github/todo/[FILENAME]-TODO.md`

**Remember:** This is just the starting point. Don't worry if it's rough or incomplete - that's what the next steps are for!
