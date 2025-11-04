#!/data/data/com.termux/files/usr/bin/bash
# Field4 vs Field5 Live Monitor
clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║       FIELD4 vs FIELD5 - LIVE COMPARISON              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

while true; do
    tput cup 4 0
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "FIELD4 (OLD - with extinction loop):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -5 ~/ariannamethod/logs/field4.log | grep -E "Iteration|EXTINCTION" || echo "  [waiting...]"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "FIELD5 (FIXED - stable!):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -5 ~/ariannamethod/logs/field5.log | grep "Iteration" || echo "  [waiting...]"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PROCESSES:"
    ps aux | grep "python3.*field_core" | grep -v grep | awk '{printf "  PID %-6s CPU %-5s MEM %-5s\n", $2, $3"%", $4"%"}'
    echo ""
    echo "Press Ctrl+C to stop monitoring"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    sleep 5
done
