#!/bin/sh
# 拒绝任何指向主干的推送。安装在 .git/hooks/pre-push
# 用法：cp scripts/deny-main-push.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push
# 说明见 issue-pr-loop/references/pr-contract.md 的「本地钩子」一节。
remote="$1"
zero=0000000000000000000000000000000000000000

while read -r local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/heads/main|refs/heads/master|refs/heads/slim)
      echo "拒绝直推主干：$remote_ref" >&2
      echo "所有改动必须经 PR：git push origin <你的分支>，再开 PR。" >&2
      exit 1
      ;;
  esac
done

exit 0
