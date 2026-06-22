"""
notify.py — Windows 任务完成弹窗通知

用法:
  python tools/notify.py "Agent 完成"
  python tools/notify.py "Agent 完成" "风云项目"
  python tools/notify.py --hook-json "Agent 完成"

技术:mshta vbscript popup,5 秒自动消失,不阻塞主流程
"""
import json
import subprocess
import sys


def notify(msg: str, title: str = "风云 ai-wechat-pipeline", timeout: int = 5):
    msg = msg.replace('"', "'").replace("\n", " ")
    title = title.replace('"', "'")
    cmd = (
        f'mshta vbscript:Execute('
        f'"CreateObject(""WScript.Shell"").Popup ""{msg}"", {timeout}, ""{title}"", 64:close"'
        f')'
    )
    subprocess.Popen(cmd, shell=True)


if __name__ == "__main__":
    hook_json = "--hook-json" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--hook-json"]
    msg = args[0] if len(args) > 0 else "任务完成"
    title = args[1] if len(args) > 1 else "风云 ai-wechat-pipeline"
    notify(msg, title)
    if hook_json:
        print(json.dumps({}, ensure_ascii=False))
    else:
        print(f"通知已弹出: {msg}")
