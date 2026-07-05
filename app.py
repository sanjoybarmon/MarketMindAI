import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import textwrap
import warnings
warnings.filterwarnings('ignore')

# ─── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="MarketMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F0F2F5; }
    .stButton>button {
        width: 100%;
        background-color: #1565C0;
        color: white;
        border-radius: 8px;
        padding: 0.6em;
        font-weight: bold;
        border: none;
        font-size: 16px;
    }
    .stButton>button:hover { background-color: #0D47A1; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #1565C0;
    }
    .metric-label {
        font-size: 13px;
        color: #666;
        margin-top: 4px;
    }
    div[data-testid="stSidebar"] {
        background-color: #1A237E;
    }
    div[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# SMART COLUMN MAPPER
# ═══════════════════════════════════════════════════════════

def auto_detect_columns(df):
    """Automatically detect required columns from any dataset."""
    def normalize(s):
        return s.lower().replace(' ', '').replace('_', '').strip()

    normalized = [normalize(c) for c in df.columns]
    original   = list(df.columns)

    patterns = {
        'customer_id': ['customerid', 'clientid', 'userid',
                        'memberid', 'buyerid', 'custid'],
        'date':        ['invoicedate', 'orderdate', 'purchasedate',
                        'transactiondate', 'date', 'datetime'],
        'amount':      ['totalamount', 'totalprice', 'totalrevenue',
                        'netamount', 'gmv', 'revenue', 'ordervalue',
                        'saleamount', 'ordertotal', 'subtotal',
                        'sales', 'netsales', 'totalsales',
                        'lineamount', 'linetotal', 'extensionamt'],
        'invoice':     ['invoiceno', 'invoice_no', 'invoice',
                        'orderid', 'transactionid','txnid', 'receiptid'],
        'quantity':    ['quantity', 'qty', 'units', 'itemcount'],
        'price': ['unitprice', 'unit_price', 'itemprice', 'priceperunit', 'rate', 'price']
    }

    detected = {}
    for field, keywords in patterns.items():
        for i, col in enumerate(normalized):
            if col in keywords:
                detected[field] = original[i]
                break

    if detected.get('amount') == detected.get('price') and \
       'quantity' in detected:
        detected.pop('amount', None)

    return detected


def validate_mapping(df, mapping):
    """Validate that mapped columns have correct data types."""
    errors = []

    if mapping.get('customer_id'):
        nulls = df[mapping['customer_id']].isnull().sum()
        if nulls > len(df) * 0.5:
            errors.append(
                f"⚠️ Customer ID has {nulls:,} missing values (>{50}%)")

    if mapping.get('date'):
        try:
            pd.to_datetime(df[mapping['date']].head(100))
        except:
            errors.append("❌ Date column cannot be parsed as datetime")

    if mapping.get('amount'):
        if not pd.api.types.is_numeric_dtype(df[mapping['amount']]):
            try:
                pd.to_numeric(df[mapping['amount']], errors='coerce')
            except:
                errors.append("❌ Amount column is not numeric")

    return errors


def prepare_standard_df(df, mapping, has_invoice, has_quantity, has_price):
    """Convert any dataset to standard format for analysis."""
    standard = pd.DataFrame()

    col = df[mapping['customer_id']]
    if pd.to_numeric(col, errors='coerce').notna().mean() > 0.8:
        standard['Customer ID'] = pd.to_numeric(col, errors='coerce')
    else:
        codes, _ = pd.factorize(col)
        standard['Customer ID'] = codes + 1

    date_col = df[mapping['date']].astype(str)
    parsed = pd.to_datetime(date_col, dayfirst=True, errors='coerce')
    if parsed.isna().mean() > 0.5:
        parsed = pd.to_datetime(
            date_col.str.replace('.', '-', regex=False),
            dayfirst=True, errors='coerce')
    standard['InvoiceDate'] = parsed

    def parse_numeric(series):
        """Handle European number format: 6,95 → 6.95"""
        try:
            result = pd.to_numeric(series, errors='coerce')
            if result.isna().mean() > 0.5:
                result = pd.to_numeric(
                    series.astype(str).str.replace(',', '.'),
                    errors='coerce')
            return result
        except:
            return pd.to_numeric(series, errors='coerce')

    if mapping.get('amount'):
        standard['TotalAmount'] = parse_numeric(df[mapping['amount']])
    elif has_quantity and has_price:
        qty   = parse_numeric(df[mapping['quantity']])
        price = parse_numeric(df[mapping['price']])
        standard['TotalAmount'] = qty * price
    else:
        standard['TotalAmount'] = np.nan

    if has_invoice and mapping.get('invoice'):
        standard['Invoice'] = df[mapping['invoice']].astype(str)
    else:
        standard['Invoice'] = (
            standard['Customer ID'].astype(str) + '_' +
            standard['InvoiceDate'].dt.strftime('%Y%m%d')
        )

    standard = standard.dropna(
        subset=['Customer ID', 'InvoiceDate', 'TotalAmount'])
    standard = standard[standard['TotalAmount'] > 0]
    standard = standard[standard['Customer ID'] >= 0]
    standard['Customer ID'] = standard['Customer ID'].astype(int)

    return standard.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════
# DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════

@st.cache_data
def load_raw(file):
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=encoding)
            if len(df.columns) > 1:
                return df
        except:
            continue
    file.seek(0)
    return pd.read_csv(file, encoding='latin-1', errors='ignore')


@st.cache_data
def build_rfm(df_json):
    import io
    df = pd.read_json(io.StringIO(df_json))
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    reference_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm = df.groupby('Customer ID').agg(
        Recency   = ('InvoiceDate', lambda x: (reference_date - x.max()).days),
        Frequency = ('Invoice',     'nunique'),
        Monetary  = ('TotalAmount', 'sum')
    ).reset_index()

    def safe_qcut(series, q, labels):
        try:
            return pd.qcut(series, q=q, labels=labels,
                       duplicates='drop').astype(int)
        except ValueError:
            unique_vals = series.nunique()
            actual_q = min(q, unique_vals)
            if actual_q < 2:
                return pd.Series([1] * len(series), index=series.index)
            actual_labels = labels[:actual_q]
            try:
                return pd.qcut(series, q=actual_q,
                          labels=actual_labels,
                          duplicates='drop').astype(int)
            except:
                return pd.cut(series, bins=actual_q,
                         labels=actual_labels,
                         duplicates='drop').astype(int)

    rfm['R_Score'] = safe_qcut(rfm['Recency'],   5, [5,4,3,2,1])
    rfm['F_Score'] = safe_qcut(rfm['Frequency'].rank(method='first'), 5, [1,2,3,4,5])
    rfm['M_Score'] = safe_qcut(rfm['Monetary'],  5, [1,2,3,4,5])

    def assign_segment(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        if   r >= 4 and f >= 4 and m >= 4: return 'Champions'
        elif r >= 3 and f >= 3 and m >= 3: return 'Loyal Customers'
        elif r >= 4 and f <= 2:            return 'New Customers'
        elif r >= 3 and f >= 2 and m >= 2: return 'Potential Loyalists'
        elif r <= 2 and f >= 3 and m >= 3: return 'At Risk'
        elif r <= 2 and f >= 4 and m >= 4: return 'Cannot Lose Them'
        elif r <= 2 and f <= 2:            return 'Lost Customers'
        else:                              return 'Needs Attention'

    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    return rfm


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🧠 MarketMind AI")
    st.markdown("*AI-Powered E-commerce Analytics*")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📂 Upload Your Sales Data (CSV)",
        type=['csv'],
        help="Supports any e-commerce CSV with customer, date & amount columns"
    )

    st.markdown("---")
    st.markdown("### 📊 Select Analysis")
    analysis = st.radio(
        "",
        ["🏠 Overview",
         "👥 RFM Segmentation",
         "📈 Sales Forecasting",
         "💡 AI Insights"],
        index=0
    )
    st.markdown("---")
    st.markdown("**MarketMind AI v1.0**")
    st.markdown("Final Year Project")


# ═══════════════════════════════════════════════════════════
# WELCOME SCREEN
# ═══════════════════════════════════════════════════════════

if uploaded_file is None:
    st.markdown("""
    <div style='text-align:center; padding: 60px 0 20px 0;'>
        <h1 style='font-size:48px; color:#1A237E;'>🧠 MarketMind AI</h1>
        <h3 style='color:#555; font-weight:400;'>
            AI-Powered E-commerce Analytics Suite
        </h3>
        <p style='color:#888; font-size:16px; margin-top:10px;'>
            Upload your sales CSV file from the sidebar to get started
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:36px;'>👥</div>
            <div class='metric-value'>RFM</div>
            <div class='metric-label'>Customer Segmentation</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:36px;'>📈</div>
            <div class='metric-value'>Forecast</div>
            <div class='metric-label'>90-Day Sales Prediction</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size:36px;'>💡</div>
            <div class='metric-value'>AI Insights</div>
            <div class='metric-label'>Automated Recommendations</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# MAIN APP (after file upload)
# ═══════════════════════════════════════════════════════════

else:
    raw_df   = load_raw(uploaded_file)
    detected = auto_detect_columns(raw_df)
    all_cols = ['(not available)'] + list(raw_df.columns)

    needs_mapping = not (
        all(k in detected for k in ['customer_id', 'date', 'amount']) or
        all(k in detected for k in ['customer_id', 'date', 'quantity', 'price'])
    )

    show_mapping = needs_mapping or st.sidebar.checkbox(
        "⚙️ Adjust Column Mapping", value=needs_mapping)

    if show_mapping:
        st.markdown("### 📋 Column Mapping")
        st.info("Map your CSV columns to the required fields below:")

        def idx(col):
            return all_cols.index(col) if col in all_cols else 0

        c1, c2 = st.columns(2)
        with c1:
            cust_col   = st.selectbox("👤 Customer ID *", all_cols,
                                       index=idx(detected.get('customer_id','')))
            date_col   = st.selectbox("📅 Date *", all_cols,
                                       index=idx(detected.get('date','')))
            amount_col = st.selectbox("💰 Total Amount", all_cols,
                                       index=idx(detected.get('amount','')))
        with c2:
            invoice_col = st.selectbox("🧾 Invoice / Order ID", all_cols,
                                        index=idx(detected.get('invoice','')))
            qty_col     = st.selectbox("📦 Quantity (if no Amount)", all_cols,
                                        index=idx(detected.get('quantity','')))
            price_col   = st.selectbox("🏷️ Unit Price (if no Amount)", all_cols,
                                        index=idx(detected.get('price','')))

        mapping = {
            'customer_id': cust_col    if cust_col    != '(not available)' else None,
            'date':        date_col    if date_col    != '(not available)' else None,
            'amount':      amount_col  if amount_col  != '(not available)' else None,
            'invoice':     invoice_col if invoice_col != '(not available)' else None,
            'quantity':    qty_col     if qty_col     != '(not available)' else None,
            'price':       price_col   if price_col   != '(not available)' else None,
        }
        has_invoice  = mapping['invoice']  is not None
        has_quantity = mapping['quantity'] is not None
        has_price    = mapping['price']    is not None

        if not mapping['customer_id'] and not mapping['date'] and \
           not mapping['amount']:
            st.error("❌ This dataset cannot be used with MarketMind AI.")
            st.markdown("""
**💡 MarketMind AI requires a transaction dataset with:**

| Required | Purpose |
|----------|---------|
| 👤 Customer ID | Identify unique customers for RFM |
| 📅 Date | Track purchase history & forecast trends |
| 💰 Amount or (Quantity × Price) | Calculate revenue |

**This looks like a Product Review dataset, not a transaction dataset.**
Please upload an order/purchase history dataset instead.
            """)
            st.stop()

        if not mapping['customer_id']:
            st.error("❌ Customer ID column is required!")
            st.stop()
        if not mapping['date']:
            st.error("❌ Date column is required!")
            st.info("⚠️ This dataset has no Date column — Sales Forecasting and RFM Analysis require purchase dates.")
            st.stop()
        if not mapping['amount'] and not (has_quantity and has_price):
            st.error("❌ Amount column is required!")
            st.info("⚠️ Please provide either a Total Amount column or both Quantity and Price columns.")
            st.stop()

        confirmed = st.button("✅ Confirm Mapping & Run Analysis")
        if confirmed:
            st.session_state['mapping']   = mapping
            st.session_state['has_inv']   = has_invoice
            st.session_state['has_qty']   = has_quantity
            st.session_state['has_price'] = has_price
            st.session_state['confirmed'] = True

        if not st.session_state.get('confirmed'):
            st.stop()

        mapping      = st.session_state['mapping']
        has_invoice  = st.session_state['has_inv']
        has_quantity = st.session_state['has_qty']
        has_price    = st.session_state['has_price']

    else:
        mapping      = detected
        has_invoice  = 'invoice'  in detected
        has_quantity = 'quantity' in detected
        has_price    = 'price'    in detected
        if has_quantity and has_price and \
           mapping.get('amount') == mapping.get('price'):
            mapping.pop('amount', None)

    for err in validate_mapping(raw_df, mapping):
        st.warning(err)

    missing_required = []
    if not mapping.get('customer_id'):
        missing_required.append("👤 **Customer ID** column")
    if not mapping.get('date'):
        missing_required.append("📅 **Date** column")
    if not mapping.get('amount') and not (
        mapping.get('quantity') and mapping.get('price')):
        missing_required.append(
            "💰 **Amount** column (or both Quantity + Price)")

    if missing_required:
        st.error("❌ Cannot proceed — Required columns are missing:")
        for col in missing_required:
            st.markdown(f"- {col}")
        st.markdown("---")
        st.info("""
**💡 What your dataset needs for MarketMind AI:**

| Required | Purpose |
|----------|---------|
| 👤 Customer ID | Identify unique customers for RFM |
| 📅 Date | Track purchase history & trends |
| 💰 Amount or (Quantity × Price) | Calculate revenue |

**This tool works with transaction/order datasets, not product or review datasets.**

Please upload a dataset with order/purchase history.
        """)
        st.stop()

    with st.spinner("🔄 Processing your data..."):
        df = prepare_standard_df(
            raw_df, mapping, has_invoice, has_quantity, has_price)

    if len(df) == 0:
        st.error("❌ No valid rows found after processing!")
        st.markdown("""
**Possible reasons:**
- Date column cannot be parsed as a valid date
- Amount/Price column has no numeric values
- Customer ID column is empty

Please check your dataset and try again.
        """)
        st.stop()

    if len(df) < 100:
        st.warning(
            f"⚠️ Only {len(df):,} valid rows found. "
            f"Results may not be statistically reliable. "
            f"We recommend at least 100+ transactions.")

    date_range = (df['InvoiceDate'].max() - 
                  df['InvoiceDate'].min()).days
    if date_range < 30:
        st.warning(
            f"⚠️ Dataset covers only {date_range} days. "
            f"Sales Forecasting needs at least 30 days of data.")

    rfm = build_rfm(df.to_json(date_format='iso'))

    def check_forecast_ready():
        if date_range < 30:
            st.error(
                f"❌ Sales Forecasting needs at least 30 days of data. "
                f"Your dataset has only {date_range} days.")
            st.info(
                "💡 Please upload a dataset with longer purchase history.")
            return False
        if df['Customer ID'].nunique() < 10:
            st.error(
                "❌ Sales Forecasting needs at least 10 unique customers.")
            return False
        return True

    def check_rfm_ready():
        if df['Customer ID'].nunique() < 10:
            st.error(
                "❌ RFM Analysis needs at least 10 unique customers. "
                f"Your dataset has only "
                f"{df['Customer ID'].nunique()} customers.")
            st.info(
                "💡 Please upload a dataset with more customers.")
            return False
        return True

    st.sidebar.success(
        f"✅ {len(df):,} rows loaded\n"
        f"👥 {df['Customer ID'].nunique():,} customers")


    # ═══════════════════════════════════════════════════════
    # PAGE 1 — OVERVIEW
    # ═══════════════════════════════════════════════════════

    if analysis == "🏠 Overview":
        st.markdown("## 📊 Business Overview")

        total_revenue   = df['TotalAmount'].sum()
        total_orders    = df['Invoice'].nunique()
        total_customers = df['Customer ID'].nunique()
        avg_order       = total_revenue / total_orders

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Total Revenue",    f"£{total_revenue:,.0f}")
        c2.metric("📦 Total Orders",     f"{total_orders:,}")
        c3.metric("👥 Total Customers",  f"{total_customers:,}")
        c4.metric("🛒 Avg Order Value",  f"£{avg_order:,.2f}")
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Monthly Revenue Trend")
            df['Month'] = df['InvoiceDate'].dt.to_period('M')
            monthly = df.groupby('Month')['TotalAmount'].sum()
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(monthly.index.astype(str), monthly.values,
                    marker='o', color='#1565C0', linewidth=2.5, markersize=4)
            ax.fill_between(range(len(monthly)),
                            monthly.values, alpha=0.1, color='#1565C0')
            ax.set_xlabel("Month")
            ax.set_ylabel("Revenue (£)")
            n_months = len(monthly)
            if n_months > 24:
                ax.set_xticks(range(0, n_months, 6))
                ax.set_xticklabels(
                    [monthly.index.astype(str)[i] 
                     for i in range(0, n_months, 6)],
                    rotation=45, ha='right', fontsize=7)
            elif n_months > 12:
                ax.set_xticks(range(0, n_months, 3))
                ax.set_xticklabels(
                    [monthly.index.astype(str)[i] 
                     for i in range(0, n_months, 3)],
                    rotation=45, ha='right', fontsize=7)
            else:
                ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            st.pyplot(fig); plt.close()

        with col2:
            if 'Country' in raw_df.columns:
                st.markdown("#### Top 10 Countries by Revenue")
                top_c = df.copy()
                top_c['Country'] = raw_df['Country'].values[:len(df)]
                top_c = top_c.groupby('Country')['TotalAmount'].sum()\
                             .sort_values(ascending=True).tail(10)
                chart_label = "Country"
            else:
                st.markdown("#### Top 10 Customers by Revenue")
                top_c = df.groupby('Customer ID')['TotalAmount'].sum()\
                          .sort_values(ascending=True).tail(10)
                top_c.index = [f"Customer {i}" for i in top_c.index]
                chart_label = "Customer"

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.barh(top_c.index, top_c.values, color='#4CAF50')
            ax.xaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
            ax.set_xlabel("Revenue")
            ax.tick_params(axis='x', rotation=30, labelsize=8)
            ax.grid(True, alpha=0.3, axis='x')
            fig.tight_layout()
            st.pyplot(fig); plt.close()

        st.markdown("---")
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("#### Revenue by Day of Week")
            df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()
            day_order   = ['Monday','Tuesday','Wednesday',
                           'Thursday','Friday','Saturday','Sunday']
            day_revenue = df.groupby('DayOfWeek')['TotalAmount']\
                            .sum().reindex(day_order, fill_value=0)
            colors = ['#FF5722' if d == day_revenue.idxmax()
                      else '#90CAF9' for d in day_order]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(day_revenue.index, day_revenue.values, color=colors)
            ax.tick_params(axis='x', rotation=30)
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
            ax.grid(True, alpha=0.3, axis='y')
            fig.tight_layout()
            st.pyplot(fig); plt.close()

        with col4:
            st.markdown("#### Revenue by Hour of Day")
            df['Hour'] = df['InvoiceDate'].dt.hour
            hour_revenue = df.groupby('Hour')['TotalAmount'].sum()

            if hour_revenue.index.max() == 0 and \
               hour_revenue.index.min() == 0:
                st.info(
                    "⚠️ This dataset has no time information — "
                    "only dates are available.")
            else:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.fill_between(hour_revenue.index,
                                hour_revenue.values,
                                alpha=0.4, color='#9C27B0')
                ax.plot(hour_revenue.index, hour_revenue.values,
                        color='#9C27B0', linewidth=2.5)
                ax.set_xlabel("Hour (24h)")
                ax.set_ylabel("Revenue (£)")
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
                ax.grid(True, alpha=0.3)
                fig.tight_layout()
                st.pyplot(fig); plt.close()


    # ═══════════════════════════════════════════════════════
    # PAGE 2 — RFM SEGMENTATION
    # ═══════════════════════════════════════════════════════

    elif analysis == "👥 RFM Segmentation":
        st.markdown("## 👥 RFM Customer Segmentation")
        if not check_rfm_ready():
            st.stop()

        champions = rfm[rfm['Segment'] == 'Champions']
        lost      = rfm[rfm['Segment'] == 'Lost Customers']

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("👥 Total Customers", f"{len(rfm):,}")

        with c2:
            st.metric("🏆 Champions", f"{len(champions):,}")
            st.markdown(
                f"<span style='background:#E8F5E9; color:#2E7D32; "
                f"padding:3px 10px; border-radius:12px; font-size:13px; font-weight:600;'>"
                f" {len(champions)/len(rfm)*100:.1f}% of total customers</span>",
                unsafe_allow_html=True)

        with c3:
            st.metric("⚠️ Lost Customers", f"{len(lost):,}")
            st.markdown(
                f"<span style='background:#FFEBEE; color:#C62828; "
                f"padding:3px 10px; border-radius:12px; font-size:13px; font-weight:600;'>"
                f" {len(lost)/len(rfm)*100:.1f}% of total customers</span>",
                unsafe_allow_html=True)

        st.markdown("---")

        colors_map = {
            'Champions':          '#2196F3',
            'Loyal Customers':    '#4CAF50',
            'Potential Loyalists':'#8BC34A',
            'New Customers':      '#00BCD4',
            'Needs Attention':    '#FF9800',
            'At Risk':            '#FF5722',
            'Cannot Lose Them':   '#9C27B0',
            'Lost Customers':     '#9E9E9E'
        }

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Segment Distribution")
            seg_counts = rfm['Segment'].value_counts()
            colors     = [colors_map.get(s,'#90CAF9') for s in seg_counts.index]
            fig, ax    = plt.subplots(figsize=(7, 7))
            ax.pie(seg_counts.values, labels=seg_counts.index,
                   colors=colors, autopct='%1.1f%%',
                   startangle=90, textprops={'fontsize': 9})
            fig.tight_layout()
            st.pyplot(fig); plt.close()

        with col2:
            st.markdown("#### Revenue by Segment")
            seg_rev    = rfm.groupby('Segment')['Monetary']\
                            .sum().sort_values(ascending=True)
            bar_colors = [colors_map.get(s,'#90CAF9') for s in seg_rev.index]
            fig, ax    = plt.subplots(figsize=(7, 7))
            ax.barh(seg_rev.index, seg_rev.values, color=bar_colors)
            ax.xaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
            ax.tick_params(axis='x', rotation=30, labelsize=8)
            ax.grid(True, alpha=0.3, axis='x')
            fig.tight_layout()
            st.pyplot(fig); plt.close()

        st.markdown("---")
        st.markdown("#### 📋 Segment Detail Table")
        seg_table = rfm.groupby('Segment').agg(
            Customers     = ('Customer ID', 'count'),
            Avg_Recency   = ('Recency',     'mean'),
            Avg_Frequency = ('Frequency',   'mean'),
            Avg_Monetary  = ('Monetary',    'mean'),
            Total_Revenue = ('Monetary',    'sum')
        ).round(1).sort_values('Total_Revenue', ascending=False)
        st.dataframe(seg_table, use_container_width=True)


    # ═══════════════════════════════════════════════════════
    # PAGE 3 — SALES FORECASTING
    # ═══════════════════════════════════════════════════════

    elif analysis == "📈 Sales Forecasting":
        st.markdown("## 📈 Sales Forecasting (Prophet)")
        if not check_forecast_ready():
            st.stop()

        with st.spinner("🔄 Training Prophet model... (30–60 seconds)"):
            from prophet import Prophet

            daily = df.groupby(df['InvoiceDate'].dt.date)['TotalAmount']\
                      .sum().reset_index()
            daily.columns = ['ds', 'y']
            daily['ds']   = pd.to_datetime(daily['ds'])
            daily         = daily.sort_values('ds').reset_index(drop=True)

            model  = Prophet(
                yearly_seasonality   = True,
                weekly_seasonality   = True,
                daily_seasonality    = False,
                seasonality_mode     = 'multiplicative',
                changepoint_prior_scale = 0.05
            )
            model.fit(daily)
            future   = model.make_future_dataframe(periods=90)
            forecast = model.predict(future)
            forecast['yhat']       = forecast['yhat'].clip(lower=0)
            forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
            forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)

        future_only = forecast[forecast['ds'] > daily['ds'].max()]

        c1, c2, c3 = st.columns(3)
        c1.metric("📅 Forecast Period", "90 Days")
        c2.metric("💰 Expected Revenue",
                  f"£{future_only['yhat'].sum():,.0f}")
        best_row = future_only.loc[future_only['yhat'].idxmax()]
        with c3:
            st.metric("📈 Best Day", best_row['ds'].strftime('%d %b %Y'))
            st.markdown(
                f"<span style='background:#E8F5E9; color:#2E7D32; "
                f"padding:3px 10px; border-radius:12px; font-size:13px; font-weight:600;'>"
                f" £{best_row['yhat']:,.0f} expected revenue</span>",
                unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("#### Revenue Forecast — Next 90 Days")
        actual    = forecast[forecast['ds'] <= daily['ds'].max()]
        predicted = forecast[forecast['ds'] >  daily['ds'].max()]

        fig, ax = plt.subplots(figsize=(14, 5))
        ax.fill_between(forecast['ds'],
                        forecast['yhat_lower'], forecast['yhat_upper'],
                        alpha=0.15, color='#2196F3', label='Confidence Interval')
        ax.plot(actual['ds'],    actual['yhat'],
                color='#2196F3', linewidth=1.5,
                label='Historical Fit', alpha=0.8)
        ax.plot(predicted['ds'], predicted['yhat'],
                color='#FF5722', linewidth=2.5,
                label='90-Day Forecast', linestyle='--')
        ax.scatter(daily['ds'], daily['y'],
                   color='#4CAF50', s=4, alpha=0.4, label='Actual Sales')
        ax.axvline(x=daily['ds'].max(), color='black',
                   linestyle=':', linewidth=1.5, alpha=0.7,
                   label='Forecast Start')
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig); plt.close()

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Weekly Seasonality")
            day_names   = ['Monday','Tuesday','Wednesday',
                           'Thursday','Friday','Saturday','Sunday']
            weekly_eff  = forecast.groupby(
                forecast['ds'].dt.dayofweek)['weekly'].mean()
            bar_colors  = ['#FF5722' if i == weekly_eff.idxmax()
                           else '#90CAF9' for i in range(7)]
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(day_names, weekly_eff.values, color=bar_colors)
            ax.tick_params(axis='x', rotation=30)
            ax.set_ylabel("Seasonality Effect")
            ax.grid(True, alpha=0.3, axis='y')
            fig.tight_layout()
            st.pyplot(fig); plt.close()

        with col2:
            st.markdown("#### Yearly Seasonality")
            month_names_all = ['Jan','Feb','Mar','Apr','May','Jun',
                               'Jul','Aug','Sep','Oct','Nov','Dec']
            yearly_eff = forecast.groupby(
                forecast['ds'].dt.month)['yearly'].mean()

            available_months = yearly_eff.index.tolist()
            month_names_avail = [month_names_all[m-1] 
                                 for m in available_months]
            bar_colors2 = [
                '#FF5722' if i == yearly_eff.idxmax()
                else '#4CAF50' for i in available_months
            ]

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(month_names_avail, yearly_eff.values,
                   color=bar_colors2)
            ax.set_ylabel("Seasonality Effect")
            ax.grid(True, alpha=0.3, axis='y')
            fig.tight_layout()
            st.pyplot(fig); plt.close()


    # ═══════════════════════════════════════════════════════
    # PAGE 4 — AI INSIGHTS  (now with click-to-reveal actions)
    # ═══════════════════════════════════════════════════════

    elif analysis == "💡 AI Insights":
        st.markdown("## 💡 Automated Business Insights")

        total_revenue   = rfm['Monetary'].sum()
        total_customers = len(rfm)
        champions       = rfm[rfm['Segment'] == 'Champions']
        lost            = rfm[rfm['Segment'] == 'Lost Customers']
        at_risk         = rfm[rfm['Segment'] == 'At Risk']
        potential       = rfm[rfm['Segment'] == 'Potential Loyalists']

        df['Month']  = df['InvoiceDate'].dt.month
        monthly      = df.groupby('Month')['TotalAmount'].sum()
        month_names  = {1:'January',  2:'February', 3:'March',
                        4:'April',    5:'May',       6:'June',
                        7:'July',     8:'August',    9:'September',
                        10:'October', 11:'November', 12:'December'}
        best_month   = month_names[monthly.idxmax()]
        worst_month  = month_names[monthly.idxmin()]
        drop_pct     = (monthly.max()-monthly.min())/monthly.max()*100

        champ_pct    = len(champions)/total_customers*100
        champ_rev    = champions['Monetary'].sum()
        champ_rev_pct= champ_rev/total_revenue*100
        lost_risk    = lost['Monetary'].mean() * len(lost)

        def make_insight_items():
            items = []

            if len(champions) > 0:
                items.append({
                    'category': 'REVENUE', 'color': '#1565C0',
                    'bg': '#E3F2FD', 'icon': '💰',
                    'title': 'Champions Drive Your Business',
                    'insight': (
                        f"{len(champions)} Champions "
                        f"({champ_pct:.1f}%) generate "
                        f"£{champ_rev:,.0f} — "
                        f"{champ_rev_pct:.1f}% of total revenue."),
                    'action': (
                        f"Reward these {len(champions)} customers "
                        f"with exclusive offers to maintain loyalty.")
                })
            else:
                items.append({
                    'category': 'REVENUE', 'color': '#1565C0',
                    'bg': '#E3F2FD', 'icon': '💰',
                    'title': 'No Champions Yet',
                    'insight': (
                        "No Champions identified yet — "
                        "your top customers need more engagement "
                        "to reach Champion status."),
                    'action': (
                        "Focus on converting Loyal Customers "
                        "into Champions with exclusive rewards.")
                })

            items.append({
                'category': 'WARNING', 'color': '#E65100',
                'bg': '#FFF3E0', 'icon': '⚠️',
                'title': 'High Customer Churn Detected',
                'insight': (
                    f"{len(lost)} customers "
                    f"({len(lost)/total_customers*100:.1f}%) "
                    f"are Lost. Revenue at risk: "
                    f"£{lost_risk:,.0f}."),
                'action': (
                    "Launch a win-back campaign with 20% discount "
                    "for customers inactive over 6 months.")
            })

            if len(at_risk) > 0:
                items.append({
                    'category': 'WARNING', 'color': '#E65100',
                    'bg': '#FFF3E0', 'icon': '🔴',
                    'title': 'At-Risk Customers Need Immediate Action',
                    'insight': (
                        f"{len(at_risk)} valuable customers are "
                        f"At Risk — they used to buy frequently "
                        f"but have gone quiet."),
                    'action': (
                        f"Send personalized re-engagement emails "
                        f"to {len(at_risk)} at-risk customers "
                        f"this week.")
                })

            if len(potential) > 0:
                items.append({
                    'category': 'OPPORTUNITY', 'color': '#2E7D32',
                    'bg': '#E8F5E9', 'icon': '🚀',
                    'title': 'Potential Loyalists Ready to Upgrade',
                    'insight': (
                        f"{len(potential)} Potential Loyalists "
                        f"are close to becoming Champions."),
                    'action': (
                        f"Offer loyalty points or bundle deals "
                        f"to convert {len(potential)} customers "
                        f"into Champions.")
                })

            if monthly.idxmax() != monthly.idxmin():
                items.append({
                    'category': 'OPPORTUNITY', 'color': '#2E7D32',
                    'bg': '#E8F5E9', 'icon': '📅',
                    'title': 'Seasonal Revenue Opportunity',
                    'insight': (
                        f"{best_month} is your strongest month. "
                        f"{worst_month} is weakest — revenue "
                        f"drops {drop_pct:.0f}% vs peak."),
                    'action': (
                        f"Prepare campaigns in advance for "
                        f"{best_month}. Run promotions in "
                        f"{worst_month} to boost slow period.")
                })

            items.append({
                'category': 'FORECAST', 'color': '#6A1B9A',
                'bg': '#F3E5F5', 'icon': '📈',
                'title': 'Next 90-Day Revenue Forecast',
                'insight': (
                    "Prophet AI model has analyzed your historical "
                    "sales patterns and generated a 90-day "
                    "revenue forecast."),
                'action': (
                    "Go to Sales Forecasting tab to see the full "
                    "prediction and allocate budget accordingly.")
            })

            return items

        all_items = make_insight_items()

        # ── Card renderer with click-to-reveal action ──────
        for i in range(0, len(all_items), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(all_items):
                    continue

                item = all_items[idx]
                state_key = f"insight_open_{idx}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = False

                with col:
                    # Top part: badge + title + insight (always visible)
                    st.markdown(f"""
<div style='background:{item["bg"]};
            border-left:5px solid {item["color"]};
            border-radius:10px 10px 0 0;
            padding:20px 24px 16px 24px;
            box-shadow:0 2px 8px rgba(0,0,0,0.07);'>
    <div style='color:{item["color"]};font-weight:700;
                font-size:12px;letter-spacing:1px;margin-bottom:6px;'>
        {item["icon"]} {item["category"]}
    </div>
    <div style='font-size:16px;font-weight:700;
                color:#1A1A2E;margin-bottom:10px;'>
        {item["title"]}
    </div>
    <div style='font-size:14px;color:#37474F;line-height:1.6;'>
        {item["insight"]}
    </div>
</div>""", unsafe_allow_html=True)

                    # Toggle button
                    btn_label = "▲ Hide recommended action" if \
                        st.session_state[state_key] else \
                        "▼ Show recommended action"
                    if st.button(btn_label, key=f"toggle_{idx}"):
                        st.session_state[state_key] = \
                            not st.session_state[state_key]

                    # Bottom part: action, only if toggled open
                    if st.session_state[state_key]:
                        st.markdown(f"""
<div style='background:{item["bg"]};
            border-left:5px solid {item["color"]};
            border-radius:0 0 10px 10px;
            padding:12px 24px 18px 24px;
            margin-top:-4px;
            margin-bottom:16px;
            box-shadow:0 2px 8px rgba(0,0,0,0.07);'>
    <span style='font-size:12px;font-weight:700;
                 color:{item["color"]};'>→ ACTION: </span>
    <span style='font-size:13px;color:#444;'>
        {item["action"]}
    </span>
</div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div style='margin-bottom:16px;'></div>",
                            unsafe_allow_html=True)
