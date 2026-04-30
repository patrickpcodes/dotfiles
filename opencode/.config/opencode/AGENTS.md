## Interactive Response System

**MANDATORY**: At the end of every response, provide 3-5 **Next Action Options** labeled with letters **j, k, l, o, p**
**Format**: Each option should be a clear, actionable next step the user can choose, displayed on separate lines for easy reading
**Purpose**: Streamlines conversation flow and reduces back-and-forth communication
**User Response**: User responds with a single letter (j/k/l/o/p) to select their preferred next action
**Example Format**:
 
  **Next Actions:**
  j) Build and test the changes
  k) Add additional validation to the email service
  l) Create a new Linear issue for email template improvements
  o) Update documentation for the new email system
  p) Move on to a different task
 
  
## Code Quality Requirements

**MANDATORY OBJECT VERIFICATION**: Before implementing any code, verify all objects by reading their properties, methods, constructors, and related DTOs
**Testing**: Run dotnet test before and after changes - never leave failing tests
**Performance**: Use bulk operations, HashSet for lookups, batch database operations
**Transactions**: Always wrap multi-step database operations in transactions

## Documentation Update Requirements

**IMPORTANT**: Periodically update these files:
1. **README.md**: Development status, new features, architecture changes
2. **External Issues**: Look for LINEAR.md for instructions(if it exists). Task status, progress updates, technical decisions
3. **AGENTS.md**: Service descriptions, new patterns, architectural decisions

**Update Frequency**: After major features, architecture changes, or at minimum monthly during active development.

## Shell Command Explanations

**MANDATORY**: When providing shell commands for the user to run, include inline comments explaining:
  - What each command does
  - What special flags/options mean (e.g., -R means recursive, -p means create parent directories)
  - What symbols mean (e.g., | is pipe, && chains commands, > redirects output)
  - What the expected outcome is
**Format**: Use # comments on the same line or above each command
**Example**:
 
bash
  # Create directory and all parent directories if they don't exist
  sudo mkdir -p /var/lib/postgres/data    # -p = create parents, sudo = run as admin

  # Change ownership recursively to postgres user/group
  sudo chown -R postgres:postgres /var/lib/postgres    # -R = recursive, user:group format
 
**Purpose**: User is learning Linux - commands should be educational, not just functional

### When Starting Work
1. **Read Context**: Always start by reading AGENTS.md and README.md
2. **Become familiar with domain specific terms**: Read through UBIQUITOUS_LANGUAGE.md (if it exists) to get up to speed.
3. **Review External Task Tracking System**: Read through LINEAR.md file for instructions(if it exists).  Check assigned issues for current priorities


## General Testing Strategy

# C# applications
**Unit Tests**: Business logic and domain rules
**Integration Tests**: Database operations with TestContainers and transaction-based isolation
**Architecture Tests**: Enforce clean architecture boundaries
**Authorization Tests**: Comprehensive auth verification

### Overall comment reductions
**MANDATORY**: Let's try to limit the amount of comments left in the code.  I find a lot of comments unnessary
    - When removing code blocks, we don't really need a comment for that, our version tracking keeps track of that
    - For simple/basic logic, we don't need a comment to explain it
