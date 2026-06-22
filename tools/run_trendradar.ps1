# run_trendradar.ps1 — 启动 TrendRadar 抓取一次
#
# 解决了 Windows PowerShell 5.1 GBK 编码崩 emoji 的坑:
#   TrendRadar 输出含 ⚠ ❌ 等 emoji,Python stdout 默认走 GBK → UnicodeEncodeError → 程序退出
#   修法: PYTHONIOENCODING=utf-8 + python -X utf8 + Console.OutputEncoding=UTF8
#
# 用法:
#   .\tools\run_trendradar.ps1
#   .\tools\run_trendradar.ps1 -Background    # 后台跑
#
# 关联: WRITE_AGENT.md Preflight 红线 / preflight.ps1 救场命令

[CmdletBinding()]
param(
    [switch]$Background
)

$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$pyExe = "D:\Dev\TrendRadar\.venv\Scripts\python.exe"
$trendradarDir = "D:\Dev\TrendRadar"

# 加载 .env(EMAIL_FROM / EMAIL_PASSWORD / EMAIL_TO 等敏感信息;gitignored)
# TrendRadar loader.py 用 os.environ.get 读这些,不用 python-dotenv
$envFile = Join-Path $trendradarDir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $idx = $line.IndexOf("=")
            $key = $line.Substring(0, $idx).Trim()
            $val = $line.Substring($idx + 1).Trim().Trim('"').Trim("'")
            Set-Item -Path "env:$key" -Value $val
        }
    }
    Write-Host "[i] 已加载 $envFile 环境变量" -ForegroundColor Gray
}

if (-not (Test-Path $pyExe)) {
    Write-Host "[FAIL] 找不到 venv Python: $pyExe" -ForegroundColor Red
    Write-Host "       TrendRadar 虚拟环境可能未初始化,跑 setup-windows.bat 部署" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 启动 TrendRadar 抓取(UTF-8 模式)" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $trendradarDir

if ($Background) {
    Start-Process -FilePath $pyExe -ArgumentList "-X","utf8","-m","trendradar" `
        -WindowStyle Hidden -PassThru | Out-Null
    Write-Host "[OK] 已在后台启动 TrendRadar 抓取" -ForegroundColor Green
    Write-Host "     完成后看 D:\Dev\TrendRadar\output\latest_daily.md" -ForegroundColor Gray
} else {
    & $pyExe -X utf8 -m trendradar

    # 抓取完成后的发布流水线(顺序:存网页全文 → 公众号草稿 → 订阅者通知邮件)
    $scripts = "D:\Dev\ai-daily-website\scripts"

    # 1) 当日完整日报存进 Neon,供网站 /today 展示
    if (Test-Path "$scripts\publish_web_digest.py") {
        Write-Host "`n[i] 存当日网页全文 (/today)..." -ForegroundColor Cyan
        & $pyExe -X utf8 "$scripts\publish_web_digest.py"
    }

    # 2) 完整日报(简报版 + 阅读原文)推公众号草稿箱
    if (Test-Path "$scripts\push_wechat_draft.py") {
        Write-Host "`n[i] 推公众号草稿箱..." -ForegroundColor Cyan
        & $pyExe -X utf8 "$scripts\push_wechat_draft.py"
    }

    # 3) 给订阅者发通知邮件(链接到 /today),DirectMail 发信
    if (Test-Path "$scripts\send_digest.py") {
        Write-Host "`n[i] 群发订阅者通知邮件..." -ForegroundColor Cyan
        & $pyExe -X utf8 "$scripts\send_digest.py"
    }
}
