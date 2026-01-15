name: Full_Market_Wick_Scan
on:
  schedule:
    - cron: "15,45 1-5 * * 1-5" # 盤中執行
  workflow_dispatch: # 允許手動點擊執行
jobs:
  run-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install
        run: pip install yfinance pandas requests FinMind
      - name: Run Scan
        run: python wick_scan.py
      - name: Sync Cache
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git pull --rebase origin main
          git add sent_wick_spikes.txt
          git commit -m "Update wick cache" || echo "no changes"
          git push origin main
