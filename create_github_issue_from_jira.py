import os
import requests
import json

# Jira environment variables
jira_issue_payload = json.loads(os.getenv("JIRA_ISSUE_PAYLOAD"))

# Github environment variables
repo_owner = os.getenv("REPO_OWNER")
repo_name = os.getenv("REPO_NAME")
token = os.getenv("GITHUB_TOKEN")

jira_issue_key = jira_issue_payload.get("issue_key", "")
jira_issue_summary = jira_issue_payload.get("issue_summary", "")
jira_issue_description = jira_issue_payload.get("issue_description", "")

def create_github_issue_from_jira(jira_issue_key, jira_issue_summary, jira_issue_description, repo_owner, repo_name, token):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": f"Jira Issue: {jira_issue_key} -- {jira_issue_summary}",
        "body": f"Imported from Jira Issue {jira_issue_key}\n\n{jira_issue_description}"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"✅ GitHub issue created successfully for Jira issue {jira_issue_key}")
        print(response.json())
    else:
        print(f"❌ Failed to create GitHub issue for Jira issue {jira_issue_key}: {response.status_code}")
        print(response.text)


create_github_issue_from_jira(jira_issue_key, jira_issue_summary, jira_issue_description, repo_owner, repo_name, token)
