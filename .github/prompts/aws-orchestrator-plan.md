# AWS Agent Orchestrator Infrastructure Plan

## Task Overview

Deploy a cost-optimized AWS infrastructure to run AI services (LiteLLM, PostgreSQL, Redis, OpenCode server) on bare-metal EC2 instances with automated shutdown scheduling, and implement a Python-based agent orchestrator that integrates with Slack to manage spot instance lifecycles for on-demand AI code generation, testing, and review tasks.

## Context

- **Current state**: The `ai` project has a Podman container setup that simulates the target AWS architecture, running LiteLLM, PostgreSQL, Redis, and will include an OpenCode server. Currently local-only with no AWS deployment.

- **Related files**:
  - `ai/.devcontainer/podman-compose.yml` - Current container configuration to replicate
  - `ai/.github/prompts/agentcode-create-slack.md` - Slack integration reference
  - `infra/` - Pulumi infrastructure code (will need new stack for AI services)

- **Dependencies**:
  - AWS EC2 (bare metal instances, spot instances)
  - AWS EventBridge (scheduled shutdown/startup)
  - AWS Route 53 (DNS for `ai.traillenshq.com`)
  - AWS Systems Manager (shell access)
  - AWS Security Groups
  - Elastic IP (static public IP)
  - Nginx (reverse proxy on port 8080)
  - LiteLLM, PostgreSQL, Redis (running as systemd services, not containers)
  - OpenCode Server
  - Python 3.14 (orchestrator application)
  - Slack API (agent interface)
  - OpenCode SDK (agent implementation)

- **Constraints**:
  - Cost optimization is critical - prefer bare metal over containers to eliminate Docker/Podman overhead
  - Trade-off: sacrifice some maintainability for reduced operational costs
  - Must analyze costs for 24/7 operation vs. 7am-midnight operation
  - Services must be accessible at `https://ai.traillenshq.com` on port 8080

## Requirements

1. **EC2 Instance Specification**: Provision an EC2 instance with minimum 2 vCPUs, sufficient RAM to run LiteLLM + PostgreSQL + Redis + OpenCode server, and at least 30GB storage. Instance type must be cost-optimized for the workload.

2. **Cost Analysis**: Research and document AWS pricing for the chosen instance type running 24/7 vs. scheduled operation (7am-midnight), including compute, storage, data transfer, and Elastic IP costs. Provide monthly cost estimates for both scenarios.

3. **Automated Scheduling**: Implement AWS EventBridge rules to automatically shut down the EC2 instance overnight and start it in the morning (7am start, midnight stop) to reduce costs during non-business hours.

4. **DNS Configuration**: Use Pulumi to configure Route 53 DNS entry for `ai.traillenshq.com` pointing to the Elastic IP address allocated to the EC2 instance.

5. **Network Configuration**:
   - Allocate a single Elastic IP and associate it with the EC2 instance
   - Configure Security Group with inbound rules for port 8080 (HTTPS), SSH (restricted to Systems Manager), and any other required service ports
   - Configure outbound rules for internet access

6. **Systems Manager Access**: Set up AWS Systems Manager Session Manager on the EC2 instance to provide secure shell access without requiring SSH key management or bastion hosts.

7. **Service Deployment**: Install and configure LiteLLM, PostgreSQL, Redis, and OpenCode server as systemd services (not containers) on the EC2 instance. Services must start automatically on boot.

8. **Reverse Proxy**: Configure Nginx as a reverse proxy on the EC2 instance to route incoming traffic on port 8080 to the appropriate backend services (LiteLLM, OpenCode, etc.), matching the current Podman container setup.

9. **LiteLLM Access**: Ensure LiteLLM is accessible from OpenCode TUI/IDE, OpenCode mobile, and Continue.dev IDE running remotely, with proper authentication to prevent credential exposure. All models currently configured in Pulumi must be available.

10. **Agent Orchestrator Application**: Develop a Python 3.14 application that:
    - Accepts markdown files via command line or Slack integration
    - Launches EC2 spot instances for task processing
    - Manages spot instance lifecycle (launch, execute, shutdown)
    - Handles request queuing when multiple tasks are submitted
    - Coordinates tasks like code generation, testing, code review, and deployment automation using the OpenCode SDK

11. **Slack Integration**: Integrate the agent orchestrator with Slack to provide a conversational interface for submitting tasks and receiving results. Reference implementation details in `agentcode-create-slack.md`.

12. **Pulumi Management**: All infrastructure (EC2 instance, Elastic IP, Route 53, Security Groups, EventBridge rules, IAM roles) must be defined and managed via Pulumi in the `infra/` repository.

## Expected Behavior

- **Infrastructure deployed**: EC2 instance is running at `ai.traillenshq.com:8080` with all services accessible via Nginx reverse proxy
- **Cost visibility**: Detailed cost analysis document comparing 24/7 vs. scheduled operation, with recommendations
- **Automated operations**: EC2 instance automatically shuts down at midnight and starts at 7am via EventBridge (if scheduled mode chosen)
- **Remote access**: Users can access LiteLLM from OpenCode and Continue.dev IDE from anywhere with proper authentication
- **Secure shell**: Systems Manager Session Manager provides shell access without SSH keys
- **Agent orchestration**: Python application accepts markdown task files, spawns spot instances, executes tasks using OpenCode SDK, and returns results
- **Slack interface**: Team members can submit agent tasks via Slack and receive notifications when tasks complete
- **Infrastructure as code**: All AWS resources are version-controlled in Pulumi, allowing reproducible deployments
- **Service reliability**: Systemd ensures all services (LiteLLM, PostgreSQL, Redis, OpenCode) restart on failure and boot

## Additional Notes

### Security Considerations
- **Credential management**: Do not expose LiteLLM API keys or model credentials in logs, environment variables, or configuration files. Use AWS Secrets Manager or Parameter Store.
- **Authentication**: Implement proper authentication for LiteLLM endpoints to prevent unauthorized model access and cost abuse.
- **Network security**: Security Group rules must be tightly scoped - only allow port 8080 from specific IP ranges if possible, restrict Systems Manager access to authorized IAM principals.
- **Spot instance data**: Ensure spot instances do not store sensitive code or credentials; all task data should be ephemeral or stored in S3 with encryption.
- **Slack security**: Validate Slack webhook signatures to prevent unauthorized task submissions.

### Performance Considerations
- **Instance sizing**: Start with a conservative instance size (e.g., t3.medium or c6i.large) and monitor CPU/memory utilization. Scale up if needed.
- **LiteLLM caching**: Configure LiteLLM with appropriate caching to reduce API calls and costs.
- **Database performance**: PostgreSQL should use SSD storage (gp3 EBS volumes) for acceptable performance.
- **Spot instance startup**: Optimize spot instance AMI to include pre-installed dependencies to reduce task startup time.
- **Nginx buffering**: Configure Nginx buffering appropriately for streaming responses from LiteLLM.

### Edge Cases to Handle
- **EventBridge failures**: What happens if the shutdown event fails? Implement CloudWatch alarms to detect instances running unexpectedly.
- **Spot instance interruptions**: Agent orchestrator must handle spot instance termination gracefully and retry tasks on new instances.
- **Concurrent task limits**: Define maximum concurrent spot instances to prevent runaway costs.
- **Task timeouts**: Implement timeouts for agent tasks to prevent infinite execution and cost overruns.
- **Service failures**: Configure systemd to restart failed services automatically, but alert if restart loops occur.

### Migration/Deployment Strategy
- **Phased deployment**:
  1. Deploy EC2 instance with manual service setup first
  2. Convert to Pulumi after validating configuration
  3. Add EventBridge scheduling once stable
  4. Implement agent orchestrator incrementally (CLI first, then Slack)
- **Rollback plan**: Keep Podman container setup functional as fallback during migration. Document manual EC2 instance termination procedure.
- **Testing**: Test all services on EC2 instance before exposing externally. Validate DNS, SSL/TLS, authentication before production use.

### Constitution Compliance Notes
- **Python requirements**: Use Python 3.14 for orchestrator application, create `.venv` in repository root, never commit virtual environment
- **Pulumi standards**: Follow existing TrailLens Pulumi patterns from `infra/` repository
- **No Makefiles**: Use Python scripts or npm scripts for automation
- **Type hints**: All Python orchestrator functions must have type hints
- **Error handling**: Use specific exceptions, never bare `except:`
- **Git workflow**: Create `topic/aws-orchestrator` branch for all changes

### Open Questions
- **Instance type selection**: What is the minimum instance type that can reliably run LiteLLM + PostgreSQL + Redis + OpenCode server? (Requires benchmarking)
- **Spot instance AMI**: Should we create a custom AMI for agent tasks, or use a standard AMI and install dependencies at runtime?
- **Cost threshold**: What is the maximum acceptable monthly cost for this infrastructure? (Requires business decision)
- **SSL/TLS**: How will HTTPS be handled - AWS ACM certificate + ALB, Let's Encrypt on EC2, or Cloudflare proxy?
- **Backup strategy**: Do we need automated backups for PostgreSQL data, or is it ephemeral/reproducible?
- **Multi-region**: Should agent orchestrator support spot instances in multiple AWS regions for cost optimization?
- **Model access control**: How should we control which Slack users can access which LLM models to manage costs?

### Research Required
- Review AWS EC2 instance pricing documentation to determine cost-optimal instance type
- Research AWS spot instance pricing and interruption rates for agent orchestration workload
- Investigate best practices for securing LiteLLM deployments in production
- Review existing Slack bot implementations using OpenCode SDK (see `agentcode-create-slack.md`)
- Analyze current Pulumi infrastructure patterns in `infra/` repository to ensure consistency

## Instructions for AI Assistant

**IMPORTANT**:

- Create a TODO list for this task - DO NOT implement any changes yet
- Save the TODO list to `.github/todo/AWS-ORCHESTRATOR-TODO.md`
- The TODO must follow the structure and requirements defined in `.github/prompts/todo-template.md`
- Each TODO item must include: description, acceptance criteria, dependencies, affected files, testing requirements, risks, rollback plan
- Break work into logical phases: Prerequisites → Implementation → Testing → Documentation/Deployment
- Wait for user approval before proceeding with any implementation
- Follow Constitution standards (see `.github/copilot-instructions.md`)
- Follow language-specific coding standards in `.github/CONSTITUTION-{language}.md` files

**Process**:

1. **Read and analyze this prompt:**
   - Extract all requirements, context, constraints, and expected behavior
   - Identify affected files, components, and dependencies
   - Note applicable Constitution rules and compliance requirements
   - Flag any ambiguities or missing information

2. **Read and apply TODO template requirements:**
   - Follow ALL requirements in `.github/prompts/todo-template.md`
   - Use the file structure template provided
   - Use the TODO item structure template for each task
   - Include all required fields: priority, complexity, owner, acceptance criteria, dependencies, affected files, testing, risks, rollback plans

3. **Generate comprehensive TODO list:**
   - Break down work into 4+ logical phases
   - Assess complexity (break down any XL tasks into smaller items)
   - Map dependencies between tasks
   - Assign priorities (P0-P3) based on blocking/critical nature
   - Include Constitution compliance checklist
   - Add risks, assumptions, and open questions sections

4. **Save TODO file:**
   - Save to `.github/todo/AWS-ORCHESTRATOR-TODO.md`
   - Verify naming convention: ALL CAPS base, `-TODO` suffix, `.md` extension

5. **Present for review:**
   - Display the generated TODO list
   - Explain the phasing and key decisions
   - Wait for user approval or feedback
   - DO NOT make any code changes - you are in PLANNING MODE

6. **Iterate if needed:**
   - Address user feedback and update TODO list
   - Re-present until approved
   - Only proceed to implementation after explicit approval

**Success Criteria**:

- [ ] Prompt file analyzed completely (all sections understood)
- [ ] TODO template requirements followed (structure, fields, validation)
- [ ] TODO list saved to `.github/todo/AWS-ORCHESTRATOR-TODO.md` with correct naming
- [ ] Every requirement from prompt captured in TODO items
- [ ] All TODO items include required fields: priority, complexity, acceptance criteria, dependencies, files, testing, risks, rollback
- [ ] Work broken into logical phases with dependency ordering
- [ ] Complexity assessed (no XL items remaining without breakdown)
- [ ] Constitution compliance checklist included
- [ ] TODO list presented to user for review
- [ ] User feedback addressed (if applicable)
- [ ] No code changes made during planning - PLANNING MODE ONLY
- [ ] Implementation blocked until explicit user approval received
