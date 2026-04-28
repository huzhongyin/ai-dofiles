# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
# Functions
rbenv () {
	local command
	command="${1:-}" 
	if [ "$#" -gt 0 ]
	then
		shift
	fi
	case "$command" in
		(rehash | shell) eval "$(rbenv "sh-$command" "$@")" ;;
		(*) command rbenv "$command" "$@" ;;
	esac
}
# Shell Options
setopt nohashdirs
setopt login
# Aliases
alias -- pib='bundle exec pod install'
alias -- run-help=man
alias -- which-command=whence
# Check for rg availability
if ! (unalias rg 2>/dev/null; command -v rg) >/dev/null 2>&1; then
  alias rg='/Users/xpeng/.vscode/extensions/anthropic.claude-code-2.1.69-darwin-arm64/resources/native-binary/claude --ripgrep'
fi
export PATH='/Users/xpeng/.rbenv/shims:/Users/xpeng/.rbenv/bin:/Applications/DevEco-Studio.app/Contents/tools/hvigor/bin:/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin:/opt/homebrew/lib/ruby/gems/3.4.0/bin/:/opt/homebrew/opt/ruby/bin:/opt/homebrew/bin:/Users/xpeng/.rbenv/shims:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Library/Apple/usr/bin:/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains'
