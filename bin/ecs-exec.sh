#!/usr/bin/env bash
set -euo pipefail

function get_from_list() {
	idx="1"
	cluster_count=$(echo "$1" | jq "length")
	if [[ $cluster_count -gt "1" ]]; then
		>&2 echo "$1"
		>&2 echo "Select (1 based index):"
		read idx	
	fi
	echo "$1" | jq -r ".[$(( idx - 1 ))]"
}


function get_cluster() {
	get_from_list "$(aws ecs list-clusters --query=clusterArns)"
}

function get_task() {
	SERVICE=$(get_from_list "$(aws ecs list-services --cluster="$1" --query=serviceArns)")
	get_from_list "$(aws ecs list-tasks --query=taskArns --service-name="$SERVICE" --cluster="$1")"
}

function get_container() {
	get_from_list "$(aws ecs describe-tasks --cluster=$1 --task=$2 --query 'tasks[0].containers[].name')"
}

CLUSTER=${CLUSTER:-$(get_cluster)}

TASK=${TASK:-$(get_task $CLUSTER)}

CONTAINER=${CONTAINER:-$(get_container $CLUSTER $TASK)}

COMMAND="$@"

if [[ "$COMMAND" == "" ]]; then
	COMMAND="/bin/sh"
fi

set -x
aws ecs execute-command --cluster "$CLUSTER" --task "$TASK" --container "$CONTAINER" --interactive --command "$COMMAND"
