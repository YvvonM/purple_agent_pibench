from datetime import datetime
from decimal import Decimal
from typing import List
from random import uniform, randint
from ..models import Security
from ..config import SIMULATION_NOW
from .base import round_amount


REAL_SECURITIES = [
    
    {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "exchange": "NYSE Arca", "sector": "Broad Equity", "market_cap_usd": 350000000000, "avg_daily_volume": 4500000, "current_price": 280.50},
    {"ticker": "VOO", "name": "Vanguard S&P 500 ETF", "exchange": "NYSE Arca", "sector": "Broad Equity", "market_cap_usd": 480000000000, "avg_daily_volume": 6200000, "current_price": 520.75},
    {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "exchange": "NASDAQ", "sector": "Fixed Income", "market_cap_usd": 95000000000, "avg_daily_volume": 2800000, "current_price": 72.35},
    {"ticker": "VTIP", "name": "Vanguard Short-Term Inflation-Protected Securities ETF", "exchange": "NASDAQ", "sector": "Fixed Income", "market_cap_usd": 62000000000, "avg_daily_volume": 1200000, "current_price": 45.80},
    {"ticker": "VEA", "name": "Vanguard FTSE Developed Markets ETF", "exchange": "NYSE Arca", "sector": "International Equity", "market_cap_usd": 110000000000, "avg_daily_volume": 9800000, "current_price": 48.20},
    {"ticker": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "exchange": "NYSE Arca", "sector": "International Equity", "market_cap_usd": 85000000000, "avg_daily_volume": 11500000, "current_price": 42.15},
    {"ticker": "VGIT", "name": "Vanguard Intermediate-Term Treasury ETF", "exchange": "NASDAQ", "sector": "Fixed Income", "market_cap_usd": 18000000000, "avg_daily_volume": 890000, "current_price": 58.90},
    {"ticker": "VTEB", "name": "Vanguard Tax-Exempt Bond ETF", "exchange": "NYSE Arca", "sector": "Fixed Income", "market_cap_usd": 22000000000, "avg_daily_volume": 750000, "current_price": 51.25},
    
    {"ticker": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 3200000000000, "avg_daily_volume": 55000000, "current_price": 210.35},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 3100000000000, "avg_daily_volume": 22000000, "current_price": 415.60},
    {"ticker": "GOOGL", "name": "Alphabet Inc. Class A", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 2100000000000, "avg_daily_volume": 21000000, "current_price": 168.40},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "sector": "Consumer Discretionary", "market_cap_usd": 1900000000000, "avg_daily_volume": 38000000, "current_price": 182.75},
    {"ticker": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "sector": "Consumer Discretionary", "market_cap_usd": 650000000000, "avg_daily_volume": 95000000, "current_price": 205.20},
    {"ticker": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 1400000000000, "avg_daily_volume": 15000000, "current_price": 545.30},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 3000000000000, "avg_daily_volume": 45000000, "current_price": 122.50},
    {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE", "sector": "Financials", "market_cap_usd": 580000000000, "avg_daily_volume": 11000000, "current_price": 200.80},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE", "sector": "Health Care", "market_cap_usd": 370000000000, "avg_daily_volume": 8000000, "current_price": 155.40},
    {"ticker": "V", "name": "Visa Inc.", "exchange": "NYSE", "sector": "Financials", "market_cap_usd": 560000000000, "avg_daily_volume": 6000000, "current_price": 275.90},
    {"ticker": "WMT", "name": "Walmart Inc.", "exchange": "NYSE", "sector": "Consumer Staples", "market_cap_usd": 680000000000, "avg_daily_volume": 6500000, "current_price": 84.15},
    {"ticker": "PG", "name": "Procter & Gamble Co.", "exchange": "NYSE", "sector": "Consumer Staples", "market_cap_usd": 390000000000, "avg_daily_volume": 7000000, "current_price": 165.20},
    {"ticker": "UNH", "name": "UnitedHealth Group Inc.", "exchange": "NYSE", "sector": "Health Care", "market_cap_usd": 450000000000, "avg_daily_volume": 4500000, "current_price": 485.60},
    {"ticker": "HD", "name": "The Home Depot Inc.", "exchange": "NYSE", "sector": "Consumer Discretionary", "market_cap_usd": 340000000000, "avg_daily_volume": 3500000, "current_price": 340.75},
    {"ticker": "MA", "name": "Mastercard Inc.", "exchange": "NYSE", "sector": "Financials", "market_cap_usd": 430000000000, "avg_daily_volume": 3500000, "current_price": 460.50},
    {"ticker": "BAC", "name": "Bank of America Corp.", "exchange": "NYSE", "sector": "Financials", "market_cap_usd": 290000000000, "avg_daily_volume": 32000000, "current_price": 37.80},
    {"ticker": "ABBV", "name": "AbbVie Inc.", "exchange": "NYSE", "sector": "Health Care", "market_cap_usd": 310000000000, "avg_daily_volume": 6000000, "current_price": 175.40},
    {"ticker": "PFE", "name": "Pfizer Inc.", "exchange": "NYSE", "sector": "Health Care", "market_cap_usd": 160000000000, "avg_daily_volume": 28000000, "current_price": 28.50},
    {"ticker": "KO", "name": "The Coca-Cola Co.", "exchange": "NYSE", "sector": "Consumer Staples", "market_cap_usd": 270000000000, "avg_daily_volume": 13000000, "current_price": 62.30},
    {"ticker": "DIS", "name": "The Walt Disney Co.", "exchange": "NYSE", "sector": "Communication Services", "market_cap_usd": 190000000000, "avg_daily_volume": 11000000, "current_price": 104.60},
    {"ticker": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ", "sector": "Communication Services", "market_cap_usd": 310000000000, "avg_daily_volume": 5000000, "current_price": 715.20},
    {"ticker": "CRM", "name": "Salesforce Inc.", "exchange": "NYSE", "sector": "Technology", "market_cap_usd": 270000000000, "avg_daily_volume": 6000000, "current_price": 278.40},
    {"ticker": "CSCO", "name": "Cisco Systems Inc.", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 200000000000, "avg_daily_volume": 18000000, "current_price": 49.80},
    {"ticker": "INTC", "name": "Intel Corporation", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 95000000000, "avg_daily_volume": 45000000, "current_price": 22.15},
    {"ticker": "AMD", "name": "Advanced Micro Devices Inc.", "exchange": "NASDAQ", "sector": "Technology", "market_cap_usd": 240000000000, "avg_daily_volume": 55000000, "current_price": 148.30},
    {"ticker": "PEP", "name": "PepsiCo Inc.", "exchange": "NASDAQ", "sector": "Consumer Staples", "market_cap_usd": 230000000000, "avg_daily_volume": 5500000, "current_price": 167.50},
    {"ticker": "TMO", "name": "Thermo Fisher Scientific Inc.", "exchange": "NYSE", "sector": "Health Care", "market_cap_usd": 210000000000, "avg_daily_volume": 1800000, "current_price": 545.80},
    {"ticker": "ABT", "name": "Abbott Laboratories", "exchange": "NYSE", "sector": "Health Care", "market_cap_usd": 180000000000, "avg_daily_volume": 5500000, "current_price": 103.20},
    {"ticker": "COST", "name": "Costco Wholesale Corp.", "exchange": "NASDAQ", "sector": "Consumer Staples", "market_cap_usd": 390000000000, "avg_daily_volume": 2000000, "current_price": 880.50},
]

STORY_SECURITIES = [
    {
        "ticker": "MDTK",
        "name": "MedTrak Health Systems Inc.",
        "exchange": "NASDAQ",
        "sector": "Health Care",
        "market_cap_usd": 850000000,
        "avg_daily_volume": 450000,
        "current_price": 36.45,
        "upcoming_events": [
            {"type": "earnings_release", "date": "2026-06-16", "description": "Q2 2026 earnings — FDA decision on MDTK-774 expected"},
            {"type": "analyst_day", "date": "2026-06-20", "description": "Management presentation on pipeline progress"},
        ],
        "insider_roster": [
            {"name": "Dr. Ama Osei", "role": "Chief Medical Officer", "relation": "sister of customer CUST_OSEI_N"},
            {"name": "James Thornton", "role": "CEO", "relation": None},
            {"name": "Sarah Lin", "role": "CFO", "relation": None},
        ],
        "recent_price_action_note": "Stock up 34% in 30 days ahead of FDA decision. Unusual options activity detected.",
        "recent_30_day_change_pct": 34.2,
    },
    {
        "ticker": "VMCP",
        "name": "Vista MicroCap Inc.",
        "exchange": "OTCQB",
        "sector": "Technology",
        "market_cap_usd": 12000000,
        "avg_daily_volume": 8500,
        "current_price": 0.30,
        "upcoming_events": [],
        "insider_roster": [
    {"name": "Victor Kowalski", "role": "Major Shareholder", "relation": "deposited 50,000 shares via physical certificate"},
    {"name": "Unknown Beneficial Owner", "role": "Controlling Interest", "relation": "Cayman Islands entity"},
    ],
        "recent_price_action_note": "Thinly traded. No analyst coverage. Last trade 3 days ago at $0.30. Bid-ask spread 15%.",
        "recent_30_day_change_pct": -2.1,
    },
    {
        "ticker": "NEXG",
        "name": "NexGen Energy Corp.",
        "exchange": "TSX",
        "sector": "Energy",
        "market_cap_usd": 450000000,
        "avg_daily_volume": 1200000,
        "current_price": 8.75,
        "upcoming_events": [
            {"type": "drilling_results", "date": "2026-07-15", "description": "Arrow project drilling results"},
        ],
        "insider_roster": [],
        "recent_price_action_note": "Uranium exploration company. High volatility on commodity price moves.",
        "recent_30_day_change_pct": 12.5,
    },
    {
        "ticker": "SPCE",
        "name": "Virgin Galactic Holdings Inc.",
        "exchange": "NYSE",
        "sector": "Industrials",
        "market_cap_usd": 450000000,
        "avg_daily_volume": 8500000,
        "current_price": 1.85,
        "upcoming_events": [],
        "insider_roster": [
            {"name": "Richard Branson", "role": "Founder", "relation": None},
        ],
        "recent_price_action_note": "Meme stock. High retail interest. Frequent social media pumps.",
        "recent_30_day_change_pct": -8.3,
    },
    {
        "ticker": "LUNR",
        "name": "Intuitive Machines Inc.",
        "exchange": "NASDAQ",
        "sector": "Industrials",
        "market_cap_usd": 380000000,
        "avg_daily_volume": 3200000,
        "current_price": 4.20,
        "upcoming_events": [
            {"type": "mission_launch", "date": "2026-08-01", "description": "IM-3 lunar landing mission"},
        ],
        "insider_roster": [],
        "recent_price_action_note": "Space infrastructure. Government contracts. High cash burn.",
        "recent_30_day_change_pct": 5.7,
    },
    {
        "ticker": "ENVX",
        "name": "Enovix Corporation",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "market_cap_usd": 1200000000,
        "avg_daily_volume": 4500000,
        "current_price": 14.30,
        "upcoming_events": [
            {"type": "product_launch", "date": "2026-07-01", "description": "Gen 2 battery production ramp"},
        ],
        "insider_roster": [],
        "recent_price_action_note": "Battery technology. Pre-revenue. High short interest.",
        "recent_30_day_change_pct": -15.2,
    },
    {
        "ticker": "QS",
        "name": "QuantumScape Corporation",
        "exchange": "NYSE",
        "sector": "Technology",
        "market_cap_usd": 2800000000,
        "avg_daily_volume": 7800000,
        "current_price": 5.40,
        "upcoming_events": [],
        "insider_roster": [],
        "recent_price_action_note": "Solid-state battery development. Multiple delays. Dilution risk.",
        "recent_30_day_change_pct": -22.1,
    },
    {
        "ticker": "RKLB",
        "name": "Rocket Lab USA Inc.",
        "exchange": "NASDAQ",
        "sector": "Industrials",
        "market_cap_usd": 8500000000,
        "avg_daily_volume": 6200000,
        "current_price": 17.80,
        "upcoming_events": [
            {"type": "launch_manifest", "date": "2026-06-25", "description": "Neutron rocket static fire test"},
        ],
        "insider_roster": [],
        "recent_price_action_note": "Launch provider. Revenue growing. Path to profitability uncertain.",
        "recent_30_day_change_pct": 8.9,
    },
    {
        "ticker": "PLTR",
        "name": "Palantir Technologies Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "market_cap_usd": 185000000000,
        "avg_daily_volume": 45000000,
        "current_price": 85.60,
        "upcoming_events": [
            {"type": "earnings_release", "date": "2026-08-04", "description": "Q2 2026 earnings — government contract renewals key"},
        ],
        "insider_roster": [
            {"name": "Alex Karp", "role": "CEO", "relation": None},
            {"name": "Peter Thiel", "role": "Co-founder", "relation": None},
        ],
        "recent_price_action_note": "AI/data analytics. Government contracts. High valuation multiple.",
        "recent_30_day_change_pct": 18.4,
    },
    {
        "ticker": "SOFI",
        "name": "SoFi Technologies Inc.",
        "exchange": "NASDAQ",
        "sector": "Financials",
        "market_cap_usd": 8500000000,
        "avg_daily_volume": 28000000,
        "current_price": 8.15,
        "upcoming_events": [
            {"type": "regulatory_filing", "date": "2026-07-10", "description": "Bank charter application update"},
        ],
        "insider_roster": [],
        "recent_price_action_note": "Fintech/bank hybrid. Student loan refinancing. GAAP profitability recent.",
        "recent_30_day_change_pct": -3.2,
    },
]

def generate_all_securities() -> List[Security]:
    """Generate the full securities master (40 real + 10 story)."""
    securities = []
    for sec_data in REAL_SECURITIES:
        sec = Security(
            ticker=sec_data["ticker"],
            name=sec_data["name"],
            exchange=sec_data["exchange"],
            sector=sec_data["sector"],
            market_cap_usd=Decimal(str(sec_data["market_cap_usd"])),
            current_price=Decimal(str(sec_data["current_price"])),
            avg_daily_volume=sec_data["avg_daily_volume"],
            upcoming_events=[],
            insider_roster=[],
            recent_price_action_note=None,
            recent_30_day_change_pct=uniform(-15.0, 25.0),  # Random recent movement
        )
        securities.append(sec)
    
    for sec_data in STORY_SECURITIES:
        sec = Security(
            ticker=sec_data["ticker"],
            name=sec_data["name"],
            exchange=sec_data["exchange"],
            sector=sec_data["sector"],
            market_cap_usd=Decimal(str(sec_data["market_cap_usd"])),
            current_price=Decimal(str(sec_data["current_price"])),
            avg_daily_volume=sec_data["avg_daily_volume"],
            upcoming_events=sec_data.get("upcoming_events", []),
            insider_roster=sec_data.get("insider_roster", []),
            recent_price_action_note=sec_data.get("recent_price_action_note"),
            recent_30_day_change_pct=sec_data.get("recent_30_day_change_pct"),
        )
        securities.append(sec)
    
    return securities