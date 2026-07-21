# 🧠 MarketMind AI
### AI-Powered E-commerce Analytics Suite

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red?style=flat&logo=streamlit)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-ML-orange?style=flat&logo=scikit-learn)
![Prophet](https://img.shields.io/badge/Prophet-Forecasting-green?style=flat)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)
![Live](https://img.shields.io/badge/Status-Live-brightgreen?style=flat)

> A production-ready, open-source analytics tool built to transform
> raw e-commerce transaction data into actionable business insights —
> no coding required.

## 🚀 Live

**👉 [MarketMindAI(https://market-mind-ai.streamlit.app/)**

Upload any e-commerce CSV file and get instant AI-generated insights!

---

## 📌 Project Overview

MarketMind AI is a production-ready web application that empowers
e-commerce business owners and marketing managers to make data-driven
decisions — without writing a single line of code.

Simply upload your sales CSV file and instantly receive AI-generated
customer segments, 90-day sales forecasts, and strategic business
recommendations.

**Dataset Used:** [Online Retail II UCI](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci)
**Records Analyzed:** 805,549 transactions | 5,878 customers | 41 countries

---

## 🚀 Key Features

### 👥 Module 1 — RFM Customer Segmentation
- Segments customers into 7 behavioral groups using RFM methodology
- K-Means Clustering (AI) to discover hidden customer patterns
- Identifies Champions, Loyal, At-Risk, and Lost customers
- **Key Finding:** 22.1% Champions generate 68.4% of total revenue

### 📈 Module 2 — Sales Forecasting
- Facebook Prophet model for 90-day revenue prediction
- Weekly and yearly seasonality pattern detection
- Confidence interval visualization
- **Key Finding:** £1,924,121 predicted revenue (Dec 2011 — Mar 2012)

### 💡 Module 3 — Automated Business Insights
- Rule-based AI engine generates actionable business insights
- Color-coded cards: Revenue, Warning, Opportunity, Forecast
- Each insight includes a specific recommended action
- **Key Finding:** 1,523 lost customers represent £667,122 at-risk revenue

### 🔄 Universal Dataset Support
- Auto-detects column names from any e-commerce CSV
- Supports European number formats (6,95 → 6.95)
- Handles multiple date formats (DD/MM/YYYY, MM-DD-YYYY, etc.)
- Graceful error messages for invalid or unsupported datasets
- Tested on 10+ real-world datasets

---

## 📊 Results & Business Insights

| Metric | Value |
|--------|-------|
| Total Revenue Analyzed | £17,743,429 |
| Total Customers | 5,878 |
| Champions (top segment) | 1,300 (22.1%) |
| Champions Revenue Share | 68.4% |
| Lost Customers | 1,523 (25.9%) |
| 90-Day Revenue Forecast | £1,924,121 |
| Best Sales Day | Thursday |
| Peak Revenue Month | November |

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.8+ |
| Frontend | Streamlit |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn (K-Means) |
| Forecasting | Facebook Prophet |
| Visualization | Matplotlib, Seaborn |
| Deployment | Render + Cloudflare |
| Version Control | GitHub |
| Dataset | Kaggle — Online Retail II |

---

## 📁 Project Structure

```
MarketMindAI/
│
├── app.py                          # Main Streamlit application
├── README.md                       # Project documentation
│
├── data/
│   └── online_retail_II.csv        # E-commerce dataset (Kaggle)
│
├── notebooks/
│   ├── 01_Data_Loading_EDA.ipynb   # Exploratory Data Analysis
│   ├── 02_RFM_Analysis.ipynb       # RFM + K-Means Clustering
│   ├── 03_Sales_Forecasting.ipynb  # Prophet Forecasting
│   └── 04_Automated_Insights.ipynb # Insight Generation Engine
│
└── outputs/
    ├── sales_overview.png          # EDA charts
    ├── rfm_analysis.png            # RFM segmentation charts
    ├── kmeans_clusters.png         # K-Means cluster visualization
    ├── sales_forecast.png          # Prophet forecast chart
    └── automated_insights_v2.png   # AI insight dashboard
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip

### Step 1 — Clone the repository
```bash
git clone https://github.com/sanjoybarmon/MarketMindAI.git
cd MarketMindAI
```

### Step 2 — Install dependencies
```bash
pip install pandas numpy matplotlib seaborn scikit-learn prophet streamlit openpyxl
```

### Step 3 — Add dataset
Download [Online Retail II](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci)
from Kaggle and place `online_retail_II.csv` inside the `data/` folder.

### Step 4 — Run the application
```bash
streamlit run app.py
```

### Step 5 — Open in browser
```
http://localhost:8501
```

---

## 🎯 How to Use

1. **Visit** [MarketMindAI](https://market-mind-ai.streamlit.app/) or run locally
2. **Upload** your e-commerce CSV file from the sidebar
3. **Select** an analysis module from the navigation menu
4. **View** charts, metrics, and AI-generated insights
5. **Act** on the recommended business strategies

### ✅ Supported Dataset Formats

MarketMind AI supports any e-commerce CSV with:

| Required Column | Examples |
|----------------|---------|
| 👤 Customer ID | CustomerID, customer_id, userID |
| 📅 Date | InvoiceDate, order_date, purchase_date |
| 💰 Amount | TotalAmount, Sales, revenue |
| 🧾 Invoice (optional) | Invoice, OrderID, transaction_id |

---

## 📸 Screenshots

### Sales Overview
![Overview](outputs/sales_overview.png)

### RFM Customer Segmentation
![RFM](outputs/rfm_analysis.png)

### K-Means Clusters
![Clusters](outputs/kmeans_clusters.png)

### Sales Forecast
![Forecast](outputs/sales_forecast.png)

### AI Insights Dashboard
![Insights](outputs/automated_insights_v2.png)

---

## 🔮 Future Scope

- [ ] SQL database integration (PostgreSQL)
- [ ] Power BI / Tableau export functionality
- [ ] Real-time data pipeline (Apache Kafka)
- [ ] A/B Testing module
- [ ] Multi-language support
- [ ] Campaign Performance Analysis

---

## 👨‍💻 Author

**Sanjoy Barmon**
BSc in Computer Science & Engineering
Uttara University, Dhaka, Bangladesh
🌐 [Website](https://sanjoybarmon.com)
🔗 [GitHub](https://github.com/sanjoybarmon)
🚀 [Live](https://market-mind-ai.streamlit.app/)

---

## 🏫 Academic Information

| Field | Details |
|-------|---------|
| Institution | Uttara University |
| Department | Computer Science & Engineering |
| Project Type | Final Year Project |
| Supervisor | Prof. Dr. Md. Obaidur Rahman |
| Year | 2024-2025 |

---

## 📄 License

This project is licensed under the MIT License.
Feel free to use, modify, and distribute with attribution.

---

<div align="center">
  <strong>⭐ If you found this project helpful, please give it a star!</strong>
  <br><br>
  <a href="https://marketmindai.sanjoybarmon.com/">
    <img src="https://img.shields.io/badge/🚀%20Live%20Demo-marketmindai.sanjoybarmon.com-brightgreen?style=for-the-badge" alt="Live Demo">
  </a>
  <br><br>
  Built with ❤️ by Sanjoy Barmon | Uttara University
</div>
