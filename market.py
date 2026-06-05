import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import base64
from io import BytesIO
from playwright.sync_api import sync_playwright
import datetime
# 日本語フォントの設定（Matplotlib用）
plt.rcParams['font.family'] = 'Meiryo'

# --- 1. データ取得 ---
print("データを取得中...")
# 指標の一覧
tickers = {
    '日経平均': '^N225',
    'NYダウ': '^DJI',
    'S&P500': '^GSPC',
    'USD/JPY': 'JPY=X',
    '東証REIT': '1343.T', # 連動ETF
    '日本国債10年': '^JN09T' # データ不安定
}

# カード表示用の最新データを取得
market_data = {}
for name, ticker in tickers.items():
    try:
        # nan対策：過去10日分を取得し、空データを排除してから最新の2日分を使う
        hist = yf.Ticker(ticker).history(period="10d").dropna()
        if len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            diff = current - prev
            diff_pct = (diff) / prev * 100
            market_data[name] = {'price': current, 'diff_pct': diff_pct}
        else:
            market_data[name] = {'price': 0, 'diff_pct': 0}
    except:
        market_data[name] = {'price': 0, 'diff_pct': 0}

# グラフ用の3ヶ月データを取得
print("グラフ用データを取得中...")
try:
    # S&P500
    sp500_hist = yf.Ticker('^GSPC').history(period="3mo").dropna()
    # ★ 日経平均を追加
    nikkei_hist = yf.Ticker('^N225').history(period="3mo").dropna()
except Exception as e:
    print(f"グラフデータ取得エラー: {e}")
    sp500_hist = pd.DataFrame()
    nikkei_hist = pd.DataFrame()


# --- 2. グラフの作成 (上下2段) ---
print("グラフを作成中...")
# グラフを2つ縦に並べるための設定
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8)) # 縦に2つ、サイズを大きく
plt.subplots_adjust(hspace=0.4) # グラフ間の余白を調整

# ★ 上段：日経平均のグラフ
if not nikkei_hist.empty:
    ax1.plot(nikkei_hist.index, nikkei_hist['Close'], color='#2E8B57', linewidth=2)
    ax1.set_title('日経平均 (3 Months)', fontsize=14, color='#333333')
    ax1.grid(True, linestyle='--', alpha=0.5)
else:
    ax1.text(0.5, 0.5, '日経平均データなし', horizontalalignment='center', verticalalignment='center')

# ★ 下段：S&P500のグラフ
if not sp500_hist.empty:
    ax2.plot(sp500_hist.index, sp500_hist['Close'], color='#4682B4', linewidth=2) # 色を変えて区別
    ax2.set_title('S&P500 (3 Months)', fontsize=14, color='#333333')
    ax2.grid(True, linestyle='--', alpha=0.5)
else:
    ax2.text(0.5, 0.5, 'S&P500データなし', horizontalalignment='center', verticalalignment='center')

plt.tight_layout()

# グラフ画像をBase64文字列に変換
buffer = BytesIO()
plt.savefig(buffer, format='png', transparent=True)
buffer.seek(0)
image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
plt.close()


# --- 3. HTMLのデザイン作成 ---
print("デザインを組み立て中...")
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")

# 指標カードを作る関数
def make_card(name, price, diff_pct):
    if price == 0:
        return f"""
        <div style="background: white; border: 2px solid #ddd; border-radius: 8px; padding: 15px; width: 200px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
            <div style="font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;">{name}</div>
            <div style="font-size: 16px; color: #999;">データ取得エラー</div>
        </div>
        """
    color = "#d32f2f" if diff_pct < 0 else "#388e3c"
    sign = "+" if diff_pct > 0 else ""
    # 書式調整
    if "金利" in name:
        price_format = f"{price:.3f}%"
    elif "JPY" in name:
        price_format = f"{price:,.2f}"
    else:
        price_format = f"{price:,.2f}"
    
    return f"""
    <div style="background: white; border: 2px solid #ddd; border-radius: 8px; padding: 15px; width: 200px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
        <div style="font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;">{name}</div>
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="font-size: 24px; font-weight: bold;">{price_format}</span>
            <span style="background: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{sign}{diff_pct:.2f}%</span>
        </div>
    </div>
    """

# カードを並べる（3行2列）
cards_html = "".join([make_card(k, v['price'], v['diff_pct']) for k, v in market_data.items()])

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Meiryo', sans-serif; background: linear-gradient(to bottom, #f0f4f8, #e0e8f0); padding: 30px; margin: 0; }}
        .header {{ font-size: 28px; font-weight: bold; color: #1a365d; margin-bottom: 20px; border-bottom: 3px solid #1a365d; padding-bottom: 10px; }}
        .cards-container {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; max-width: 750px; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); display: inline-block; }}
    </style>
</head>
<body>
    <div class="header">朝のマーケットメモ ({today_str})</div>
    <div class="cards-container">
        {cards_html}
    </div>
    <div class="chart-container">
        <img src="data:image/png;base64,{image_base64}" alt="Market Charts">
    </div>
</body>
</html>
"""

# --- 4. 画像化 ---
print("最終的な画像を生成中...")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    # 画像のサイズに合わせて、ビューポート（描画領域）を少し大きく設定
    page.set_viewport_size({"width": 850, "height": 1300}) 
    page.set_content(html_content)
    # グラフ描画完了を待つ時間を少し長めに設定
    page.wait_for_timeout(2000) 
    # 画像全体をスクリーンショット
    page.locator("body").screenshot(path="morning_market_report.png")
    browser.close()

print("完了しました！デスクトップの画像が更新されました。")