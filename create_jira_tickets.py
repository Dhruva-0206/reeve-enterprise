import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

jira_url = os.getenv("JIRA_URL")
jira_user = os.getenv("JIRA_USERNAME")
jira_token = os.getenv("JIRA_API_TOKEN")

print(f"Connecting to {jira_url}...")
jira = JIRA(server=jira_url, basic_auth=(jira_user, jira_token))

project_key = "KAN"

tickets = [
    {
        "summary": "Implement baseline PPO algorithm for HighwayEnv",
        "description": "Create train_ppo.py to serve as the baseline without safety constraints. Needs to integrate with stable_baselines3 and track metrics via MLflow.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Design Safe PPO reward wrapper",
        "description": "Develop a custom reward wrapper in safe_reward_wrapper.py that incorporates collision penalties and safety lambda parameters.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Add MLflow tracking for safety metrics",
        "description": "Update training scripts to log collision rates, average speed, and safety lambda values to MLflow during training.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Bug: train_safeppo.py crashes when lambda=0.0",
        "description": "When passing safety_lambda=0.0, the reward calculation throws a division by zero error in the wrapper.",
        "issuetype": {"name": "Bug"}
    },
    {
        "summary": "Write core evaluation scripts",
        "description": "Create run_core_evaluation.sh to run multi-seed evaluations and output statistical significance tests.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Create plotting utilities for radar charts",
        "description": "In generate_plots.py, add functionality to generate radar charts comparing PPO and Safe PPO across safety and efficiency metrics.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Update README.md with setup instructions",
        "description": "Add clear installation steps, requirements.txt usage, and instructions for running the train_safeppo.py script.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Bug: MLflow artifact upload failing on large models",
        "description": "When saving the final PPO model, MLflow throws a timeout error if the model exceeds 50MB.",
        "issuetype": {"name": "Bug"}
    },
    {
        "summary": "Implement behavior evaluation callbacks",
        "description": "Create a custom callback for stable_baselines3 that records video of the agent's behavior every 100 episodes.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Research continuous action spaces for steering",
        "description": "Investigate moving from discrete actions (lane changes) to continuous steering angles for more realistic driving behavior.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Optimize environment step speed",
        "description": "Profiling shows HighwayEnv step() is bottlenecking training. Investigate vectorization or disabling rendering during training.",
        "issuetype": {"name": "Task"}
    },
    {
        "summary": "Add unit tests for reward calculation",
        "description": "Write pytest cases for the SafeRewardWrapper to ensure collision penalties scale correctly with speed.",
        "issuetype": {"name": "Task"}
    }
]

created_issues = []
for t in tickets:
    issue_dict = {
        'project': {'key': project_key},
        'summary': t['summary'],
        'description': t['description'],
        'issuetype': t['issuetype'],
    }
    try:
        new_issue = jira.create_issue(fields=issue_dict)
        print(f"Created issue {new_issue.key}: {new_issue.fields.summary}")
        created_issues.append(new_issue.key)
    except Exception as e:
        print(f"Failed to create issue {t['summary']}: {e}")

print(f"Successfully created {len(created_issues)} tickets.")
