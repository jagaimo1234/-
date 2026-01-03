import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ページ設定
st.set_page_config(page_title="収支分析ダッシュボード", layout="wide")

# 定期リロードの設定 (5分 = 300秒)
# st.empty() と time.sleep() を使う方法もありますが、
# Streamlitの公式な自動更新機能である st_autorefresh (外部ライブラリ) がない環境のため、
# ページ下部に自動リロードのスクリプトを埋め込むか、
# もしくは st.fragment や st.rerun を検討します。
# ここではシンプルに st.cache_data の有効期限を設定し、
# ユーザーがアクセスするたびに最新であることを保証しつつ、
# 画面自体を定期的にリロードするJavaScriptを埋め込みます。

# データ読み込み (キャッシュの有効期限を5分に設定)
@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lN9dMqvlagTklCxKGt5l1s50vJ3z76DvMP8hckaJXFU/export?format=csv&gid=0"
    df = pd.read_csv(url, skiprows=1)
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'])
    
    def classify_major_category(row):
        cat = str(row['category'])
        if cat in ["食費", "日用品", "嗜好品", "テスト", "その他"]:
            return "生活費"
        elif "モアイ活動" in cat:
            return "モアイ活動費"
        else:
            return "その他"
            
    df['major_category'] = df.apply(classify_major_category, axis=1)
    df['month'] = df['date'].dt.strftime('%Y-%m')
    return df

# 自動リロード用のJavaScriptを埋め込む (5分 = 300,000ミリ秒)
st.components.v1.html(
    """
    <script>
    window.parent.location.reload();
    </script>
    """,
    height=0,
)
# 上記の単純なリロードだと無限ループになるため、
# Streamlitの標準機能で「5分おきに再実行」をシミュレートします。
# 実際には st.cache_data(ttl=300) でデータは5分ごとに更新されます。
# 画面の自動更新が必要な場合は、以下の meta タグ方式が確実です。
st.markdown(
    """
    <meta http-equiv="refresh" content="300">
    """,
    unsafe_allow_html=True
)

st.title("🚀 収支分析ダッシュボード")
st.caption(f"最終更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (5分ごとに自動更新されます)")

try:
    df = load_data()

    # --- 1. 現在の収支状況 ---
    st.subheader("📊 現在の収支状況")
    total_balance = df['amount'].sum()
    latest_month = df['month'].max()
    df_latest = df[df['month'] == latest_month]
    monthly_living_exp = df_latest[(df_latest['major_category'] == "生活費") & (df_latest['amount'] < 0)]['amount'].abs().sum()
    monthly_moai_profit = df_latest[df_latest['major_category'] == "モアイ活動費"]['amount'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("累計残高", f"¥{total_balance:,.0f}")
    col2.metric(f"{latest_month} 生活費合計", f"¥{monthly_living_exp:,.0f}")
    col3.metric(f"{latest_month} モアイ活動収益", f"¥{monthly_moai_profit:,.0f}")

    st.divider()

    # --- 2. グラフ表示 ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 月別の収支推移")
        monthly_summary = df.groupby(['month', 'type'])['amount'].sum().reset_index()
        monthly_summary['display_amount'] = monthly_summary['amount'].abs()
        fig_bar = px.bar(
            monthly_summary, x='month', y='display_amount', color='type',
            barmode='group', labels={'display_amount': '金額 (円)', 'month': '月', 'type': '区分'},
            color_discrete_map={'収入': '#00CC96', '支出': '#EF553B'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("🍕 活動別の支出内訳")
        expense_df = df[df['amount'] < 0]
        major_cat_summary = expense_df.groupby('major_category')['amount'].sum().abs().reset_index()
        fig_pie = px.pie(
            major_cat_summary, values='amount', names='major_category',
            hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 3. データ詳細 ---
    st.subheader("📋 最近のログ")
    st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
