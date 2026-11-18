# Turns Pi's --mode json events into readable log lines; non-JSON lines pass through.
#   pi -p --mode json ... 2>&1 | jq --unbuffered -rR -f readable-events.jq
# Shows the agent's thinking and text in full, each command as one short line,
# and command output only when it failed.
def short($n): split("\n")[0] | if length > $n then .[:$n] + "…" else . end;
(fromjson? // {type: "raw", line: .}) as $e
| if $e.type == "raw" then $e.line
  elif $e.type == "message_end" and $e.message.role == "assistant" then
    $e.message.content[]
    | if .type == "thinking" then "~ thinking: " + .thinking
      elif .type == "text" then "> " + .text
      else empty end
  elif $e.type == "tool_execution_start" then
    "$ " + (if $e.toolName == "bash" then $e.args.command else "\($e.toolName) \($e.args | tostring)" end | short(100))
  elif $e.type == "tool_execution_end"
       and ($e.isError or (($e.result.structuredContent.exit_code // 0) != 0)) then
    ($e.result.structuredContent.exit_code // null) as $code
    | "  [error\(if $code then " exit \($code)" else "" end)] "
      + ([$e.result.content[]? | select(.type == "text") | .text] | join(" ") | short(200))
  else empty end
