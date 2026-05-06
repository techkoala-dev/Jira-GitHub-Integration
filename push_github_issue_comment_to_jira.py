import base64
import os
import requests


# Repo based environment variables
repo_name = os.getenv("REPO_NAME")
repo_owner = os.getenv("REPO_OWNER")

# Issue/Comment based environment variables
issue_number = int(os.getenv("ISSUE_NUMBER"))
issue_comment = os.getenv("COMMENT_BODY")
issue_comment_id = os.getenv("COMMENT_ID")
issue_title = os.getenv("ISSUE_TITLE")
comment_author = os.getenv("COMMENT_AUTHOR")

# Global environment variables
token = os.getenv("GITHUB_TOKEN")
project_name = os.getenv("GITHUB_PROJECT_NAME")

# Jira environment variables
jira_email = os.getenv("JIRA_EMAIL")
jira_api_token = os.getenv("JIRA_API_TOKEN")
jira_domain = os.getenv("JIRA_DOMAIN")
jira_label = os.getenv("JIRA_LABEL")


headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"                
}

def get_jira_issue_key_from_github_issue(issue_title,delimiter=" -- "):
    print(f"Extracting Jira issue key from GitHub issue title: {issue_title}")
    jira_issue_key = issue_title.split(delimiter)[0].replace("Jira Issue: ", "").strip() if delimiter in issue_title else None
    print(f"Extracted Jira issue key: {jira_issue_key}")
    return jira_issue_key


def check_if_comment_is_for_jira(comment_body):
    # Simple Check: if comment contains "/CLIENT", we treat it as intended for Jira
    return "/CLIENT" in comment_body.upper()


def push_comment_to_jira(jira_issue_key, comment_body, is_public=True):
    credentials = f"{jira_email}:{jira_api_token}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json"
    }
    url = f"https://{jira_domain}/rest/servicedeskapi/request/{jira_issue_key}/comment"
    payload = {
        "body": comment_body,
        "public": is_public
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"✅ Comment posted comment: {comment_body} successfully on Jira issue: {jira_issue_key}")
        print(response.json())
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def check_if_issue_is_linked_to_jira(repo_owner, repo_name, issue_number, project_name, jira_label):
    # Define the GraphQL query to check issue labels and linked projects
    graphql_endpoint = "https://api.github.com/graphql"

    # The query checks for labels and project links on the issue
    query = """
    query($owner: String!, $repo: String!, $issueNumber: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $issueNumber) {
          labels(first: 10) {
            nodes {
              name
            }
          }
          projectItems(first: 10) {
            nodes {
              project {
                title
                number
              }
            }
          }
        }
      }
    }
    """

    # Set the variables for the query
    variables = {
        "owner": repo_owner,
        "repo": repo_name,
        "issueNumber": issue_number
    }

    # Execute the GraphQL query
    response = requests.post(
        graphql_endpoint,
        json={"query": query, "variables": variables},
        headers=headers
    )

    # Process the response
    if response.status_code == 200:
        data = response.json()
        issue_data = data.get("data", {}).get("repository", {}).get("issue", {})
        labels = [label["name"] for label in issue_data.get("labels", {}).get("nodes", [])]
        projects = [item["project"]["title"] for item in issue_data.get("projectItems", {}).get("nodes", [])]

        print(f"Labels on issue #{issue_number}: {labels}")
        print(f"Projects linked to issue #{issue_number}: {projects}")

        # Check if any label contains the specified Jira label and if it's linked to a project with the specified Jira project name
        is_linked_to_jira = any(jira_label in label for label in labels) and any(project_name in project for project in projects)
        print(f"Is issue #{issue_number} linked to Jira? {'Yes' if is_linked_to_jira else 'No'}")
        
        return is_linked_to_jira
    else:
        print(f"❌ Failed to fetch issue data: {response.status_code} - {response.text}")
        return False


def push_comment_to_jira_if_intended(repo_owner, repo_name, issue_number, issue_title, comment_body, project_name, jira_label):
    if check_if_comment_is_for_jira(comment_body):
        print("Comment is intended for Jira. Checking if issue is linked to Jira...")
        if check_if_issue_is_linked_to_jira(repo_owner, repo_name, issue_number, project_name, jira_label):
            jira_issue_key = get_jira_issue_key_from_github_issue(issue_title)
            if jira_issue_key:
                push_comment_to_jira(jira_issue_key, comment_body)
            else:
                print("❌ Failed to extract Jira issue key from comment.")
        else:
            print("Issue is not linked to Jira. Skipping comment push.")
    else:
        print("Comment is not intended for Jira. Skipping.")


push_comment_to_jira_if_intended(repo_owner, repo_name, issue_number, issue_title, issue_comment, project_name, jira_label)
