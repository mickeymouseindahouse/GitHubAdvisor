# GitHub Repository Finder 🔍

An intelligent Streamlit chat application that helps users find the best GitHub repositories for their needs using AI-powered search and analysis. Built with LangGraph for agentic workflows and leveraging OpenAI's GPT models and GitHub's REST API.

## Features

- 🤖 **AI-Powered Query Understanding**: Uses OpenAI's GPT to understand and parse user requirements
- 🔍 **Intelligent Repository Search**: Searches GitHub with optimized queries based on user needs
- 🏗️ **AI-Generated Class Diagrams**: Creates visual class diagrams for repositories using OpenAI and Graphviz
- 📊 **Comprehensive Repository Analysis**: Analyzes multiple metrics including:
  - Stars and contributors
  - Pull request merge times
  - Issue response times
  - Commit activity patterns
  - Release frequency
  - Code quality indicators
- 🏆 **Smart Ranking System**: Ranks repositories using a composite score considering multiple factors
- 💬 **Chat Interface**: Interactive Streamlit chat interface for natural conversations
- 📈 **Visual Metrics**: Rich displays of repository metrics and comparisons

## Architecture

The application uses an **agentic LangGraph workflow** with the following components:

1. **Query Parser**: Analyzes user input to extract search terms and requirements
2. **Repository Searcher**: Uses GitHub API to find relevant repositories
3. **Repository Analyzer**: Gathers detailed metrics for each repository
4. **Class Diagram Generator**: Creates visual class diagrams using OpenAI and Graphviz
5. **Ranking Engine**: Scores and ranks repositories based on multiple criteria
6. **Response Generator**: Creates natural language explanations of recommendations

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- GitHub personal access token (optional, for higher rate limits)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd github-repository-finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here
```

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

1. **Start a conversation**: Type your repository requirements in natural language
   - Example: "I need a Python web framework for building REST APIs"
   - Example: "Find me a JavaScript library for data visualization"
   - Example: "I'm looking for a machine learning framework with good documentation"
   - Example: "Show me a class diagram for a React state management library"

2. **Review recommendations**: The AI will analyze your query and present the top repositories with detailed metrics

3. **View class diagrams**: When requested, the system will generate visual class diagrams showing the architecture of the recommended repositories

4. **Explore metrics**: Each recommendation includes:
   - Repository statistics (stars, contributors, language)
   - Activity metrics (last updated, commit frequency)
   - Pull request analytics (merge times, open PRs)
   - Release information
   - Quality indicators

## Repository Scoring Algorithm

Repositories are ranked using a composite score based on:

- **Popularity** (stars): Up to 1,000 points
- **Community** (contributors): Up to 500 points  
- **Activity** (recent updates): Up to 300 points
- **Maintenance** (PR merge speed): Up to 200 points
- **Stability** (issues-to-stars ratio): Up to 100 points

## API Rate Limits

- **Without GitHub token**: 60 requests/hour
- **With GitHub token**: 5,000 requests/hour

For heavy usage, it's recommended to provide a GitHub personal access token.

## Project Structure

```
├── app.py                      # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── github_agent.py         # Main LangGraph agent
│   ├── github_api.py           # GitHub API client
│   ├── repository_analyzer.py  # Repository analysis logic
│   └── class_diagram_generator.py  # Class diagram generation using OpenAI + Graphviz
├── requirements.txt
├── .env.example
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

1. **API Rate Limits**: Add a GitHub token to your `.env` file
2. **OpenAI API Errors**: Ensure your OpenAI API key is valid and has credits
3. **Slow Response Times**: The app analyzes repositories in real-time; expect 10-30 seconds for results

### Support

Create an issue in this repository for bug reports or feature requests.
