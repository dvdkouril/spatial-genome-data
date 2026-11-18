# Turns Pi's --mode json events into readable log lines; non-JSON lines pass through.
#   pi -p --mode json ... 2>&1 | jq --unbuffered -rR -f readable-events.jq
def cut($n): if length > $n then .[:$n] + " [... \(length - $n) more chars]" else . end;
(fromjson? // {type: "raw", line: .}) as $e
| if $e.type == "raw" then $e.line
  elif $e.type == "message_end" and $e.message.role == "assistant" then
    $e.message.content[]
    | if .type == "thinking" then "~ thinking: " + (.thinking | cut(600))
      elif .type == "text" then "> " + .text
      else empty end
  elif $e.type == "tool_execution_start" then
    "$ \($e.toolName): " + (if $e.toolName == "bash" then $e.args.command else ($e.args | tostring) end | cut(1000))
  elif $e.type == "tool_execution_end" then
    ([$e.result.content[]? | select(.type == "text") | .text] | join("\n") | cut(1500))
    | (if $e.isError then "  [error] " else "  " end) + gsub("\n"; "\n  ")
  else empty end
