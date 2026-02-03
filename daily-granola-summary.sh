#!/bin/bash

# Daily Granola Meeting Summary Script
# Runs Claude Code to summarize today's meetings and email them

# Config - set to "off" to disable without removing cron job
# DISABLED: Using AWS Lambda architecture instead (Zapier -> Lambda -> DynamoDB -> Digest)
ENABLED="off"

# Check if disabled
if [ "$ENABLED" != "on" ]; then
    echo "$(date): Script disabled, skipping"
    exit 0
fi

# Log file for debugging
LOG_FILE="$HOME/granola-summary.log"

echo "$(date): Starting daily Granola summary" >> "$LOG_FILE"

# Run Claude Code with the prompt
# --dangerously-skip-permissions allows automated execution without prompts
# --allowedTools restricts to only Granola and Gmail tools for safety
claude -p "Fetch all my Granola meetings from today ($(date +%Y-%m-%d)).

For each meeting, apply these filters to decide if it should be summarized:
1. SKIP any meeting titled '1984 Partner Meeting'
2. SKIP internal meetings where ALL other attendees have @1984.vc email addresses
3. SKIP meetings with other venture capitalists - identified by email addresses containing 'vc' or 'capital' (case insensitive)

For each meeting that passes the filters, create a concise summary with key discussion points, decisions made, and action items. Then send a single email to both samit@1984.vc and 1984bot@1984.vc with subject 'Daily Meeting Summary - $(date +%Y-%m-%d)' containing all the summaries.

If no meetings pass the filters today, do not send any email." \
    --allowedTools "mcp__granola__*,mcp__google-workspace__send_gmail_message" \
    --dangerously-skip-permissions \
    2>&1 >> "$LOG_FILE"

echo "$(date): Completed daily Granola summary" >> "$LOG_FILE"
