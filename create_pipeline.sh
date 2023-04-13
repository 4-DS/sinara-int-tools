#!/bin/bash
#set -euxo pipefail
set -euo pipefail
# Parse arguments
while [ $# -gt 0 ]; do
    if [[ $1 == *"--"* ]]; then
        v="${1/--/}"
        declare $v="$2"
    fi
    shift
done

if [[ -z "${organization:-}" ]]; then
  read -p "Please, enter the GitHub organization: " organization
fi
if [[ -z "${token:-}" ]]; then
  read -s -p "Please, enter the GitHub token for managing repositories: " token
fi

echo ""

if [[ -z "${pipeline_name:-}" ]]; then
  read -p "Please, enter your pipeline name [default=pipeline]: " pipeline_name
fi

if [[ -z "${step_count:-}" ]]; then
  read -p "Please, enter a number of steps in your pipeline [default=1]: " step_count
fi

read -p "Enter folder to clone pipeline steps to: " pipeline_folder
if [[ -z "$pipeline_folder" ]]; then
  pipeline_folder="$(pwd)"
fi

GITHUB_ORG="${organization:-}"
GITHUB_TOKEN="${token:-}"
PIPELINE_NAME="${pipeline_name:-pipeline}"
STEP_COUNT="${step_count:-1}"
GIT_CRED_STORE_TIMEOUT=3600

steps=()
set +e
i=1

while (( $i<=$STEP_COUNT ));
do
    
    if [[ -z "${step_name_template:-}" ]]; then
        while : ; do
            read -p "Please, enter $i step name of your pipeline [default=step$i] : " step_name
            if [[ " ${steps[*]} " =~ " ${step_name} " ]] && [[ ! -z "${step_name}" ]]; then
               echo -e "Step $step_name aleady exists, choose different name"
            else
               break
            fi
        done
        STEP_NAME="${step_name:-step$i}"
    else
        STEP_NAME="${step_name_template}${i}"
    fi

    curl \
      -X POST \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $GITHUB_TOKEN"\
      -H "X-GitHub-Api-Version: 2022-11-28" \
      https://api.github.com/orgs/$GITHUB_ORG/repos \
      -d '{"name":"'"$PIPELINE_NAME-$STEP_NAME"'","description":"This is your '"$i"' step in pipeline '"${PIPELINE_NAME}"'","homepage":"https://github.com","private":false,"has_issues":true,"has_projects":true,"has_wiki":true}'

    steps+=( $STEP_NAME )

    i=$((i+1))
done

read -p "Please, enter your Git user name (default=jovyan): " git_username
read -p "Please, enter your Git user email (default=jovyan@test.ru): " git_useremail

GIT_USERNAME="${git_username:-jovyan}"
GIT_USEREMAIL="${git_useremail:-jovyan@example.com}"

read -p "Your pipeline steps will be cloned soon. Would you like to store Git credentials in memory for $GIT_CRED_STORE_TIMEOUT seconds? WARINING: It may overwrite your stored github credentials. y/n (default=n): " save_git_creds

set -e
for step in ${steps[@]}; do
  cd $pipeline_folder
  git clone --recurse-submodules https://github.com/4-DS/step_template.git $PIPELINE_NAME-$step
  cd $PIPELINE_NAME-$step
  
  git config user.email "$GIT_USEREMAIL"
  git config user.name "$GIT_USERNAME"

  git remote set-url origin https://github.com/$GITHUB_ORG/$PIPELINE_NAME-$step.git

  sed -i "s/\"step_template\"/\"${step}\"/g" ./params/step_params.json
  sed -i "s/\"pipeline\"/\"${PIPELINE_NAME}\"/g" ./params/pipeline_params.json
  
  git add -A
  git commit -m "Set step and pipeline parameters"
  
  git reset $(git commit-tree HEAD^{tree} -m "a new Sinara step")
  
  if [[ ${save_git_creds} == "y" ]]; then
      git config credential.helper 'cache --timeout='$GIT_CRED_STORE_TIMEOUT''
      (echo url=https://github.com; echo username=$GITHUB_ORG; echo password=$GITHUB_TOKEN; echo ) | git credential approve  
  fi  
  
  git push
done

echo "Now you can go through the steps' folders in $pipeline_folder and declare interfaces as you need"

