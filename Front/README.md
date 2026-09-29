# SOA_Expo_roandai_2024_12_26



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://roandaiserver.ddns.net:81/Felipec3/soa_expo_roandai_2024_12_26.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations](https://roandaiserver.ddns.net:81/Felipec3/soa_expo_roandai_2024_12_26/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

## Description
New SOD is the migration of the SOD project, which was originally developed using Flutter for desktop and Python. With the migration, the project now uses Expo, a framework that enables both web and mobile development, as well as PrimeReact for creating charts. On the backend, Python continues to be used.

What is SOD?
SOD stands for Segregation of Duties. New SOD helps identify risks in roles, employees, and subsidiaries within the same organization, caused by conflicting permissions or assigned functions.

In addition, the new SOD front end aims to integrate NetSuite in the future, as well as a ticketing system.

This repository includes several branches: `charts`, `dev`, and `main`. The `prime` branch is used to test Prime React, while `roandai` branch is a customized version of the project for our team.

This is related to the [New_SOD](https://roandaiserver.ddns.net:81/arturoroa/new_sod) project.

# How to Run

## Locally

1. Clone the repository:
```
git clone https://roandaiserver.ddns.net:81/Felipec3/soa_expo_roandai_2024_12_26
```

2. Navigate to the cloned repository folder. In the branch main install the required dependencies:
```
git checkout main
npm install
```

2. Run the app
```
npx expo start --web
```

## On roandaiserver

GitLab CI/CD is configured in the branch main for this project, so be sure to commit your local changes and push them to the repository to trigger the pipeline.