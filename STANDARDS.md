# CodePulse Repo Guidelines and Standards

This markdown file outlines CodePulse's project structure, coding standards, branch naming conventions, and commit naming conventions

## CodePulse Project Structure

```
CodePulse/
├── backend/                  # Python backend application
│   ├── app/                  # Main application directory
│   │   ├── __init__.py       # App initialization
│   │   ├── main.py           # Application entry point
│   │   ├── models/           # Database models
│   │   ├── routes/           # API route handlers
│   │   ├── services/         # Business logic layer
│   │   ├── utils/            # Utility functions
│   │   └── config.py         # Configuration settings
│   ├── tests/                # Backend tests
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment variables template
│
├── frontend/                # JavaScript/React frontend
│   ├── public/              # Static files
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API service calls
│   │   ├── utils/           # Utility functions
│   │   ├── styles/          # CSS/styling files
│   │   ├── App.js           # Main app component
│   │   └── index.js         # Entry point
│   ├── package.json         # Node dependencies
│   └── .env.example         # Environment variables template
│
├── docs/                     # Project documentation
│   ├── CodePulse_Class_Diagram.png
│   ├── CodePulse_ER_Diagram.png
│   ├── CodePulse_UseCaseDiagram.drawio.png
│   ├── CodePulse_Design_&_Architecture.pdf
│   └── CodePulse_Requirements_Analysis.pdf
├── README.md                 # Project overview
└── STANDARDS.md              # This file
```

## Documentation

The `docs/` folder contains project documentation and diagrams:

- **CodePulse_Class_Diagram.png** - UML class diagram showing system architecture and relationships
- **CodePulse_ER_Diagram.png** - Entity-Relationship diagram for database schema
- **CodePulse_UseCaseDiagram.drawio.png** - Use case diagram illustrating system functionality
- **CodePulse_Design_&_Architecture.pdf** - Detailed design and architecture specifications
- **CodePulse_Requirements_Analysis.pdf** - Project requirements and analysis documentation

## Coding Standards

### Frontend (JavaScript)

#### Naming Conventions
- **Files**: Use PascalCase for component files (`UserProfile.js`), camelCase for utilities (`apiClient.js`)
- **Components**: PascalCase (`UserProfile`, `NavigationBar`)
- **Variables/Functions**: camelCase (`userData`, `fetchUserData`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`, `MAX_RETRY_COUNT`)

#### Code Style
- Use ES6+ syntax (arrow functions, destructuring, spread operators)
- Use functional components with React Hooks
- Limit component files to 300 lines; split larger components
- Use meaningful variable names (avoid single letters except in loops)
- Add JSDoc comments for complex functions
- Use async/await for asynchronous operations

#### React Best Practices
- One component per file
- Keep components small and focused
- Use prop-types or TypeScript for type checking
- Avoid inline styles; use CSS modules or styled-components
- Use `useState` and `useEffect` appropriately
- Implement error boundaries for production
- Memoize expensive computations with `useMemo`

#### File Organization
- Group related functionality in directories
- Keep components close to where they're used
- Separate presentational and container components
- Use index.js for clean imports

### Backend (Python)

#### Naming Conventions
- **Files/Modules**: Use snake_case (`user_service.py`, `auth_utils.py`)
- **Classes**: PascalCase (`UserModel`, `AuthService`)
- **Functions/Variables**: snake_case (`get_user_data`, `user_id`)
- **Constants**: UPPER_SNAKE_CASE (`DATABASE_URL`, `TOKEN_EXPIRY`)
- **Private methods**: Prefix with underscore (`_validate_token`)

#### Code Style
- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Limit line length to 88 characters (Black formatter default)
- Use docstrings for all classes, functions, and modules
- Use list comprehensions for simple iterations
- Use context managers (`with` statements) for resource management

#### Python Best Practices
- Use virtual environments for dependency isolation
- Validate all input data
- Use environment variables for configuration
- Implement proper error handling with custom exceptions
- Log important operations and errors
- Use async/await for I/O-bound operations
- Follow DRY (Don't Repeat Yourself) principle
- Write unit tests for all business logic

#### Project Structure Best Practices
- Separate concerns: routes, services, models
- Keep routes thin; business logic in services
- Use dependency injection for testability
- Implement middleware for cross-cutting concerns
- Use database migrations for schema changes

## Branches
- `main` is the production ready branch
- `<first_name>-branch` are branches to be integrated when modules/features are completed
- Branch naming should be descriptive: `<first_name>-<feature-name>` (e.g., `aiden-user-authentication`)

## Workflow
1. Create your branch from main: `git checkout -b <first_name>-<feature-name>`
2. Develop and commit regularly with meaningful commit messages
3. Write and run tests for your feature
4. Ensure code follows the standards outlined in this document
5. Make a pull request when feature has been thoroughly tested and completed
6. Request code review from at least one team member
7. Address review comments and update PR
8. Merge branch into main for a new release after approval

## Pull Request Guidelines
- Provide a clear description of changes
- Reference any related issues or tickets
- Include screenshots for UI changes
- Ensure all tests pass
- Update documentation if needed
- Keep PRs focused and reasonably sized

## Commit Structure

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build, etc.)
- `ci`: CI/CD configuration changes

### Examples
```
feat(auth): add user login functionality

Implemented JWT-based authentication with refresh tokens.
Added login endpoint and token validation middleware.

Closes #123
```

```
fix(api): resolve data fetching timeout issue

Increased timeout threshold and added retry logic
for external API calls.
```

```
docs(readme): update installation instructions

Added Python and Node.js version requirements.
```

### Commit Best Practices
- Use present tense ("add feature" not "added feature")
- Keep subject line under 50 characters
- Capitalize subject line
- Don't end subject with a period
- Use body to explain what and why, not how
- Reference issues and pull requests in footer
