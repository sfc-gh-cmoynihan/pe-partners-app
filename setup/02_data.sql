-- =============================================================================
-- PE Partners - Sample Data
-- Run AFTER 01_ddl.sql to populate all tables
-- =============================================================================

USE SCHEMA PEPARTNERS_DB.CORE;
USE WAREHOUSE COMPUTE_WH;

-- =============================================================================
-- FUNDS
-- =============================================================================

INSERT INTO FUNDS_STG (FUND_ID, FUND_NAME, STRATEGY, TOTAL_AUM_GBP, MANAGEMENT_FEE_PCT, PERFORMANCE_FEE_PCT, INCEPTION_DATE, FUND_STATUS, MINIMUM_INVESTMENT_GBP) VALUES
(1, 'PE Partners AI Growth Fund', 'Growth Equity', 480000000000.00, 1.50, 20.00, '2020-01-15', 'Active', 250000000.00),
(2, 'PE Partners AI Infrastructure Fund', 'Infrastructure', 380000000000.00, 1.25, 18.00, '2021-03-01', 'Active', 500000000.00),
(3, 'PE Partners AI Frontier Fund', 'Venture Capital', 280000000000.00, 2.00, 25.00, '2022-06-01', 'Active', 100000000.00),
(4, 'PE Partners AI Applications Fund', 'Applications', 200000000000.00, 1.75, 20.00, '2023-01-15', 'Active', 150000000.00);

-- =============================================================================
-- CUSTOMERS (LPs / Investors)
-- =============================================================================

INSERT INTO CUSTOMERS_STG (CUSTOMER_ID, FULL_NAME, COMPANY_NAME, INVESTOR_TYPE, REGION, AUM_COMMITMENT_GBP, EMAIL, PHONE, ONBOARDED_DATE, STATUS, RISK_PROFILE, RELATIONSHIP_MANAGER) VALUES
(1, 'Vanguard Capital Management (~48.51M shares / 6.46%)', 'The Vanguard Group', 'Asset Manager', 'North America', 300000000000.00, 'ownership@vanguard.com', '+1-610-669-1000', '2023-01-15', 'Active', 'Conservative', 'Michael Chen'),
(2, 'Morgan Stanley (~34.84M shares / 4.64%)', 'Morgan Stanley', 'Investment Bank', 'North America', 220000000000.00, 'ownership@morganstanley.com', '+1-212-761-4000', '2023-03-01', 'Active', 'Moderate', 'Sarah Williams'),
(3, 'State Street Corporation (~32.46M shares / 4.32%)', 'State Street Corporation', 'Asset Manager', 'North America', 180000000000.00, 'ownership@statestreet.com', '+1-617-786-3000', '2023-02-10', 'Active', 'Moderate', 'James Morton'),
(4, 'Charles Schwab Investment Management (~23.50M shares / 3.13%)', 'Charles Schwab Investment Management', 'Asset Manager', 'North America', 145000000000.00, 'ownership@schwab.com', '+1-415-667-7000', '2023-04-20', 'Active', 'Moderate', 'Michael Chen'),
(5, 'JPMorgan Chase & Co. (~19.16M shares / 2.55%)', 'JPMorgan Chase & Co.', 'Investment Bank', 'North America', 115000000000.00, 'ownership@jpmorgan.com', '+1-212-270-6000', '2023-05-01', 'Active', 'Aggressive', 'Sarah Williams'),
(6, 'Geode Capital Management, LLC (~18.37M shares / 2.45%)', 'Geode Capital Management, LLC', 'Asset Manager', 'North America', 98000000000.00, 'ownership@geodecapital.com', '+1-617-643-2200', '2023-06-15', 'Active', 'Conservative', 'James Morton'),
(7, 'Vanguard Portfolio Management LLC (~15.77M shares / 2.10%)', 'Vanguard Portfolio Management LLC', 'Asset Manager', 'North America', 84000000000.00, 'ownership@vanguard.com', '+1-610-669-1000', '2023-07-01', 'Active', 'Moderate', 'Michael Chen'),
(8, 'Capital Research Global Investors (~13.20M shares / 1.76%)', 'Capital Research Global Investors', 'Asset Manager', 'North America', 62000000000.00, 'ownership@capitalgroup.com', '+1-213-486-9200', '2023-08-10', 'Active', 'Aggressive', 'Sarah Williams'),
(9, 'Bank of America Corporation (~11.59M shares / 1.54%)', 'Bank of America Corporation', 'Investment Bank', 'North America', 52000000000.00, 'ownership@bofa.com', '+1-704-386-5681', '2023-09-01', 'Active', 'Conservative', 'James Morton');

-- =============================================================================
-- INVESTMENTS (Portfolio Positions)
-- =============================================================================

INSERT INTO INVESTMENTS_STG (INVESTMENT_ID, FUND_ID, SECURITY_NAME, TICKER, SECTOR, POSITION_TYPE, MARKET_VALUE_GBP, WEIGHT_PCT, GEOGRAPHY, ENTRY_DATE) VALUES
-- Fund 1: PE Partners Capital Partners IX
(1, 1, 'OpenAI', 'OAIP', 'AI/ML', 'LONG', 12600000000.00, 30.00, 'North America', '2020-06-01'),
(2, 1, 'Anthropic', 'ANTH', 'AI/ML', 'LONG', 10500000000.00, 25.00, 'North America', '2021-01-15'),
(3, 1, 'Scale AI', 'SCAI', 'AI/ML', 'LONG', 6300000000.00, 15.00, 'North America', '2021-09-01'),
(4, 1, 'Databricks', 'DBKS', 'Data Infrastructure', 'LONG', 4200000000.00, 10.00, 'North America', '2022-03-01'),
(5, 1, 'Cohere', 'COHR', 'AI/ML', 'LONG', 3360000000.00, 8.00, 'North America', '2022-06-15'),
(6, 1, 'Hugging Face', 'HGFC', 'AI/ML', 'LONG', 2940000000.00, 7.00, 'Europe', '2022-11-01'),
(7, 1, 'Stability AI', 'STAB', 'AI/ML', 'SHORT', -2100000000.00, 5.00, 'Europe', '2023-03-01'),
(29, 1, 'xAI', 'XAI', 'AI/ML', 'LONG', 2520000000.00, 6.00, 'North America', '2024-02-15'),
(30, 1, 'Shield AI', 'SHLD', 'Defense Tech', 'LONG', 1680000000.00, 4.00, 'North America', '2024-04-12'),
-- Fund 2: PE Partners Real Estate Partners X
(8, 2, 'CoreWeave', 'CWVE', 'Cloud Infrastructure', 'LONG', 8400000000.00, 30.00, 'North America', '2021-06-01'),
(9, 2, 'Lambda Labs', 'LMDA', 'Cloud Infrastructure', 'LONG', 5600000000.00, 20.00, 'North America', '2021-09-15'),
(10, 2, 'Cerebras Systems', 'CRBS', 'AI Hardware', 'LONG', 4200000000.00, 15.00, 'North America', '2022-01-15'),
(11, 2, 'SambaNova', 'SAMB', 'AI Hardware', 'LONG', 3360000000.00, 12.00, 'North America', '2022-05-01'),
(12, 2, 'Applied Digital', 'APLD', 'Data Centers', 'LONG', 2800000000.00, 10.00, 'North America', '2022-08-01'),
(13, 2, 'Vultr', 'VLTR', 'Cloud Infrastructure', 'LONG', 2240000000.00, 8.00, 'North America', '2023-01-15'),
(14, 2, 'WekaIO', 'WEKA', 'Data Infrastructure', 'SHORT', -1400000000.00, 5.00, 'North America', '2023-04-01'),
(31, 2, 'Crusoe Energy', 'CRUE', 'Data Centers', 'LONG', 1960000000.00, 7.00, 'North America', '2023-10-01'),
(32, 2, 'Groq', 'GROQ', 'AI Hardware', 'LONG', 1680000000.00, 6.00, 'North America', '2024-02-01'),
-- Fund 3: PE Partners Tactical Opportunities V
(15, 3, 'Cursor AI', 'CURS', 'Developer Tools', 'LONG', 3600000000.00, 20.00, 'North America', '2023-06-15'),
(16, 3, 'Perplexity AI', 'PPLX', 'AI/ML', 'LONG', 2700000000.00, 15.00, 'North America', '2023-08-01'),
(17, 3, 'Mistral AI', 'MIST', 'AI/ML', 'LONG', 2700000000.00, 15.00, 'Europe', '2023-03-01'),
(18, 3, 'Glean', 'GLEN', 'Enterprise AI', 'LONG', 2160000000.00, 12.00, 'North America', '2023-09-15'),
(19, 3, 'Runway ML', 'RNWY', 'Creative AI', 'LONG', 1800000000.00, 10.00, 'North America', '2023-04-01'),
(20, 3, 'Character AI', 'CHAI', 'Consumer AI', 'LONG', 1440000000.00, 8.00, 'North America', '2023-10-01'),
(33, 3, 'Anduril', 'ANDR', 'Defense Tech', 'LONG', 1260000000.00, 7.00, 'North America', '2024-01-20'),
(34, 3, 'Windsurf', 'WIND', 'Developer Tools', 'LONG', 900000000.00, 5.00, 'North America', '2024-05-15'),
-- Fund 4: PE Partners Energy Partners IV
(21, 4, 'Jasper AI', 'JASP', 'Content AI', 'LONG', 3000000000.00, 25.00, 'North America', '2023-03-15'),
(22, 4, 'Harvey AI', 'HRVY', 'Legal AI', 'LONG', 2400000000.00, 20.00, 'North America', '2023-05-01'),
(23, 4, 'Abridge', 'ABRD', 'Healthcare AI', 'LONG', 1800000000.00, 15.00, 'North America', '2023-07-15'),
(24, 4, 'Synthesia', 'SYNT', 'Creative AI', 'LONG', 1440000000.00, 12.00, 'Europe', '2023-09-01'),
(25, 4, 'Unlearn AI', 'UNLR', 'Healthcare AI', 'SHORT', -1200000000.00, 10.00, 'North America', '2024-01-15'),
(26, 4, 'Writer', 'WRTR', 'Content AI', 'LONG', 960000000.00, 8.00, 'North America', '2024-03-01'),
(27, 4, 'Hippocratic AI', 'HIPP', 'Healthcare AI', 'LONG', 720000000.00, 6.00, 'North America', '2024-04-10'),
(28, 4, 'ElevenLabs', 'ELVN', 'Creative AI', 'LONG', 480000000.00, 4.00, 'Europe', '2024-05-20'),
(35, 4, 'Sierra', 'SIRA', 'Enterprise AI', 'LONG', 600000000.00, 5.00, 'North America', '2024-06-03'),
(36, 4, 'Hebbia', 'HEBB', 'Enterprise AI', 'LONG', 360000000.00, 3.00, 'North America', '2024-07-10');

-- =============================================================================
-- FUND PERFORMANCE
-- =============================================================================

INSERT INTO FUND_PERFORMANCE_STG (PERF_ID, FUND_ID, REPORTING_DATE, MONTHLY_RETURN_PCT, YTD_RETURN_PCT, SHARPE_RATIO, MAX_DRAWDOWN_PCT, VOLATILITY_PCT) VALUES
-- Fund 1: PE Partners Capital Partners IX
(9, 1, '2026-05-31', 3.1000, 22.3100, 2.050, -7.5000, 13.8000),
(5, 1, '2026-06-30', 2.9500, 25.2600, 2.100, -8.2000, 14.2000),
(1, 1, '2026-07-31', 3.2400, 28.5000, 2.150, -8.2000, 14.5000),
-- Fund 2: PE Partners Real Estate Partners X
(10, 2, '2026-05-31', 2.6000, 17.0500, 1.840, -6.2000, 12.2000),
(6, 2, '2026-06-30', 2.4500, 19.5000, 1.880, -6.5000, 12.5000),
(2, 2, '2026-07-31', 2.8000, 22.3000, 1.950, -6.5000, 12.8000),
-- Fund 3: PE Partners Tactical Opportunities V
(7, 3, '2026-06-30', 3.8000, 31.3000, 2.350, -12.3000, 17.8000),
(3, 3, '2026-07-31', 4.5000, 35.8000, 2.450, -12.3000, 18.2000),
-- Fund 4: PE Partners Energy Partners IV
(11, 3, '2026-05-31', 3.2000, 27.5000, 2.260, -11.9000, 17.1000),
(8, 4, '2026-06-30', 1.8500, 16.5000, 1.680, -5.8000, 11.1000),
(12, 4, '2026-05-31', 1.6000, 14.4000, 1.620, -5.5000, 10.9000),
(4, 4, '2026-07-31', 2.1000, 18.6000, 1.720, -5.8000, 11.4000);

-- =============================================================================
-- COMPANY FILINGS
-- =============================================================================

INSERT INTO COMPANY_FILINGS (COMPANY_NAME, TICKER, FORM_TYPE, FILING_CATEGORY, FILING_DATE, SOURCE_URL) VALUES
('OpenAI', 'OAIP', 'Annual Report', 'Financial', '2026-03-15', 'https://openai.com/investor/2025-annual'),
('OpenAI', 'OAIP', 'Investor Letter', 'Governance', '2026-06-01', 'https://openai.com/investor/q2-2026'),
('OpenAI', 'OAIP', 'Funding Round', 'Capital', '2026-01-20', 'https://openai.com/investor/series-f'),
('OpenAI', 'OAIP', 'Regulatory Filing', 'Compliance', '2026-04-10', 'https://openai.com/investor/eu-aia'),
('OpenAI', 'OAIP', 'Board Update', 'Governance', '2026-07-01', 'https://openai.com/investor/board-2026'),
('Anthropic', 'ANTH', 'Annual Report', 'Financial', '2026-02-28', 'https://anthropic.com/investor/2025-annual'),
('Anthropic', 'ANTH', 'Funding Round', 'Capital', '2026-03-15', 'https://anthropic.com/investor/series-e'),
('Anthropic', 'ANTH', 'Safety Report', 'Compliance', '2026-05-20', 'https://anthropic.com/investor/rsp-2026'),
('Anthropic', 'ANTH', 'Partnership Filing', 'Strategic', '2026-06-15', 'https://anthropic.com/investor/aws-expansion'),
('Anthropic', 'ANTH', 'Investor Letter', 'Governance', '2026-07-10', 'https://anthropic.com/investor/q2-letter'),
('Mistral AI', 'MIST', 'Annual Report', 'Financial', '2026-03-01', 'https://mistral.ai/investor/2025-annual'),
('Mistral AI', 'MIST', 'Funding Round', 'Capital', '2026-02-01', 'https://mistral.ai/investor/series-c'),
('Mistral AI', 'MIST', 'Regulatory Filing', 'Compliance', '2026-04-01', 'https://mistral.ai/investor/eu-compliance'),
('Mistral AI', 'MIST', 'Government Contract', 'Strategic', '2026-05-15', 'https://mistral.ai/investor/french-gov'),
('Mistral AI', 'MIST', 'Investor Letter', 'Governance', '2026-07-05', 'https://mistral.ai/investor/h1-2026'),
('xAI (Grok)', 'XAIG', 'Annual Report', 'Financial', '2026-03-20', 'https://x.ai/investor/2025-annual'),
('xAI (Grok)', 'XAIG', 'Funding Round', 'Capital', '2026-01-10', 'https://x.ai/investor/series-b'),
('xAI (Grok)', 'XAIG', 'Infrastructure Filing', 'Strategic', '2026-04-20', 'https://x.ai/investor/memphis-dc'),
('xAI (Grok)', 'XAIG', 'Investor Letter', 'Governance', '2026-06-30', 'https://x.ai/investor/q2-2026'),
('Cursor.ai', 'CURS', 'Annual Report', 'Financial', '2026-02-15', 'https://cursor.com/investor/2025-annual'),
('Cursor.ai', 'CURS', 'Funding Round', 'Capital', '2026-04-01', 'https://cursor.com/investor/series-c'),
('Cursor.ai', 'CURS', 'Product Update', 'Strategic', '2026-06-01', 'https://cursor.com/investor/multi-agent'),
('Cursor.ai', 'CURS', 'Investor Letter', 'Governance', '2026-07-15', 'https://cursor.com/investor/q2-letter'),
('Factory.ai', 'FACT', 'Funding Round', 'Capital', '2026-03-01', 'https://factory.ai/investor/series-b'),
('Factory.ai', 'FACT', 'Product Launch', 'Strategic', '2026-05-01', 'https://factory.ai/investor/droids-v2'),
('Factory.ai', 'FACT', 'Investor Letter', 'Governance', '2026-07-20', 'https://factory.ai/investor/q2-update');

-- =============================================================================
-- COMPANY CALLS (without full transcripts for brevity - add your own)
-- =============================================================================

INSERT INTO COMPANY_CALLS (COMPANY_NAME, TICKER, CALL_TYPE, CALL_DATE, CALL_TITLE, DURATION_MINUTES, PARTICIPANTS, SENTIMENT, SENTIMENT_SCORE) VALUES
('OpenAI', 'OAIP', 'Quarterly Investor Call', '2026-07-15', 'OpenAI Q2 2026 Investor Call - GPT-5.4 Launch Update', 60, 'Sam Altman (CEO), Greg Brockman (President), Sarah Friar (CFO)', 'Positive', 0.47),
('OpenAI', 'OAIP', 'Product Deep Dive', '2026-06-01', 'OpenAI Enterprise Platform - Architecture Overview', 45, 'Brad Lightcap (COO), Srinivas Narayanan (VP Engineering)', 'Positive', 0.49),
('OpenAI', 'OAIP', 'Annual General Meeting', '2026-04-20', 'OpenAI 2026 AGM - Governance and Strategy', 90, 'Full Board, Sam Altman (CEO), Sarah Friar (CFO)', 'Neutral', 0.20),
('Anthropic', 'ANTH', 'Quarterly Investor Call', '2026-07-20', 'Anthropic Q2 2026 - Claude Opus 4 Enterprise Traction', 55, 'Dario Amodei (CEO), Daniela Amodei (President), Tom Brown (CTO)', 'Positive', 0.70),
('Anthropic', 'ANTH', 'Safety Research Update', '2026-05-10', 'Anthropic Constitutional AI - 2026 Research Directions', 40, 'Chris Olah (Research), Jan Leike (Alignment), Dario Amodei (CEO)', 'Positive', 0.45),
('Anthropic', 'ANTH', 'Partnership Call', '2026-06-20', 'Anthropic x AWS - Infrastructure Roadmap', 35, 'Daniela Amodei (President), AWS Enterprise Team', 'Positive', 0.55),
('Mistral AI', 'MIST', 'Quarterly Investor Call', '2026-07-10', 'Mistral AI H1 2026 Results - European Market Dominance', 50, 'Arthur Mensch (CEO), Guillaume Lample (CTO), Timothee Lacroix (CSO)', 'Positive', 0.31),
('Mistral AI', 'MIST', 'Product Launch Event', '2026-05-20', 'Mistral Large 3 - Next Generation European AI', 30, 'Arthur Mensch (CEO), Technical Team', 'Positive', 0.59),
('Mistral AI', 'MIST', 'Government Partnership', '2026-04-15', 'French AI Sovereignty Initiative - Mistral Partnership', 45, 'Arthur Mensch (CEO), French Digital Minister', 'Positive', 0.38),
('xAI (Grok)', 'XAIG', 'Quarterly Investor Call', '2026-07-01', 'xAI Q2 2026 - Grok 3.5 and Real-time Intelligence', 55, 'Elon Musk (CEO), Igor Babuschkin (CTO)', 'Positive', 0.45),
('xAI (Grok)', 'XAIG', 'Infrastructure Update', '2026-04-25', 'xAI Memphis Supercomputer - Full Operational Status', 40, 'Igor Babuschkin (CTO), Infrastructure Team', 'Positive', 0.61),
('xAI (Grok)', 'XAIG', 'Product Strategy', '2026-06-10', 'Grok Enterprise - Platform Strategy', 35, 'Elon Musk (CEO), Enterprise Sales Lead', 'Positive', 0.41),
('Cursor.ai', 'CURS', 'Quarterly Investor Call', '2026-07-18', 'Cursor Q2 2026 - Developer Platform Evolution', 45, 'Michael Truell (CEO), Aman Sanger (CTO)', 'Positive', 0.57),
('Cursor.ai', 'CURS', 'Product Deep Dive', '2026-06-05', 'Cursor Multi-Agent Architecture - Technical Overview', 35, 'Aman Sanger (CTO), Research Team', 'Positive', 0.46),
('Cursor.ai', 'CURS', 'Series C Announcement', '2026-04-05', 'Cursor Series C - $1.5B Funding at $12B Valuation', 30, 'Michael Truell (CEO), Lead Investors', 'Neutral', 0.27),
('Factory.ai', 'FACT', 'Quarterly Update', '2026-07-22', 'Factory.ai Q2 2026 - Autonomous Development Progress', 40, 'Matan Grinberg (CEO), CTO', 'Positive', 0.70),
('Factory.ai', 'FACT', 'Product Launch', '2026-05-05', 'Factory Droids v2 - Autonomous Software Engineering', 35, 'Matan Grinberg (CEO), Product Team', 'Positive', 0.60),
('Factory.ai', 'FACT', 'Series B Close', '2026-03-05', 'Factory.ai Series B - $500M at $2B Valuation', 25, 'Matan Grinberg (CEO), Investors', 'Positive', 0.34);

-- =============================================================================
-- REFRESH INTERACTIVE TABLES
-- =============================================================================

ALTER INTERACTIVE TABLE PEPARTNERS_DB.CORE.FUNDS_IT REFRESH;
ALTER INTERACTIVE TABLE PEPARTNERS_DB.CORE.CUSTOMERS_IT REFRESH;
ALTER INTERACTIVE TABLE PEPARTNERS_DB.CORE.INVESTMENTS_IT REFRESH;
ALTER INTERACTIVE TABLE PEPARTNERS_DB.CORE.FUND_PERFORMANCE_IT REFRESH;
